import discord
import random
import asyncio
from discord.ui import Button, View
import sentience
import sentience2
import lumberjack as l

BLACKJACK = 21
DEALER_HIT_LIMIT = 16

active_games = {}

def update_chat_context(user_id, message_content):
    if user_id in active_games:
        ctx = active_games[user_id].get('chat_context', '')
        ctx = f"{message_content}\n{ctx}"[:500]
        active_games[user_id]['chat_context'] = ctx

class BlackjackGame:
    def __init__(self, user_id, user_name, user_str, channel, cxstorage):
        self.user_id = user_id
        self.user_name = user_name
        self.user_str = user_str
        self.channel = channel
        self.cxstorage = cxstorage
        self.deck = self.create_deck()
        self.player_hand = []
        self.dealer_hand = []
        self.game_over = False
        self.bet = 0
        
    def create_deck(self):
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = []
        for _ in range(6):
            for suit in suits:
                for rank in ranks:
                    deck.append({'suit': suit, 'rank': rank})
        random.shuffle(deck)
        return deck
    
    def get_card_value(self, card):
        if card['rank'] in ['J', 'Q', 'K']:
            return 10
        elif card['rank'] == 'A':
            return 11
        else:
            return int(card['rank'])
    
    def calculate_score(self, hand):
        score = 0
        aces = 0
        for card in hand:
            score += self.get_card_value(card)
            if card['rank'] == 'A':
                aces += 1
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
        return score
    
    def deal_card(self):
        return self.deck.pop() if self.deck else None
    
    def format_hand(self, hand, hide_first=False):
        if hide_first and hand:
            return '🃏 ' + ' '.join([f"{c['rank']}{c['suit']}" for c in hand[1:]])
        return ' '.join([f"{c['rank']}{c['suit']}" for c in hand])
    
    def start_round(self):
        self.player_hand = [self.deal_card(), self.deal_card()]
        self.dealer_hand = [self.deal_card(), self.deal_card()]
        self.deck = self.create_deck()
    
    def create_embed(self, final=False, blackjack=False, bust=False):
        embed = discord.Embed(
            title="🃏 Blackjack vs Ari",
            color=0x00ff00
        )
        
        player_cards = self.format_hand(self.player_hand)
        player_score = self.calculate_score(self.player_hand)
        
        if final:
            dealer_cards = self.format_hand(self.dealer_hand)
            dealer_score = self.calculate_score(self.dealer_hand)
            embed.add_field(name="Dealer's Hand", value=f"{dealer_cards}\n**Score: {dealer_score}**", inline=False)
        else:
            embed.add_field(name="Dealer's Hand (hole card)", value=self.format_hand(self.dealer_hand, hide_first=True), inline=False)
        
        embed.add_field(name=f"{self.user_name}'s Hand", value=f"{player_cards}\n**Score: {player_score}**", inline=False)
        embed.add_field(name="Bet", value=f"{self.bet} XP", inline=True)
        embed.add_field(name="Balance", value=f"{l.get_xp_user(self.user_str) or 0} XP", inline=True)
        
        if not final and not blackjack and not bust:
            embed.set_footer(text="Hit • Stand • Double Down • Surrender")
        
        return embed
    
    async def get_ari_comment(self, game_state, extra_context=""):
        dealer_hand_val = self.format_hand(self.dealer_hand, hide_first=(game_state=='initial'))
        if game_state in ['dealer_bust', 'dealer_wins', 'player_wins', 'push', 'blackjack', 'player_surrendered']:
            dealer_hand_val = self.format_hand(self.dealer_hand)
            dealer_score = self.calculate_score(self.dealer_hand)
        else:
            dealer_score = "?"
        
        player_score = self.calculate_score(self.player_hand)
        
        prompt = f"""ari (27, nyc) is the dealer in a blackjack game vs {self.user_name}.

game info:
- ari (dealer) has: {dealer_hand_val} (score: {dealer_score})
- {self.user_name} (player) has: {self.format_hand(self.player_hand)} (score: {player_score})
- bet: {self.bet} xp
- game event: {game_state}

recent chat context:
{extra_context if extra_context else '(no recent messages)'}

make a short casual comment as ari talking to this person. keep it brief (1-2 sentences), roasty but not mean. no emojis."""

        try:
            return await sentience2.generate_text_openrouter(
                self.cxstorage,
                system_prompt=prompt,
                model='anthropic/claude-sonnet-4-6'
            )
        except:
            return "let me cook..."

class BlackjackView(View):
    def __init__(self, game: BlackjackGame):
        super().__init__(timeout=120)
        self.game = game
        self.add_item(HitButton(game))
        self.add_item(StandButton(game))
        self.add_item(DoubleDownButton(game))
        self.add_item(SurrenderButton(game))

class HitButton(Button):
    def __init__(self, game):
        super().__init__(label="Hit", style=discord.ButtonStyle.green, custom_id="hit")
        self.game = game
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message("thats not your game bro", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        card = self.game.deal_card()
        if card:
            self.game.player_hand.append(card)
            score = self.game.calculate_score(self.game.player_hand)
            
            if score > BLACKJACK:
                embed = self.game.create_embed(bust=True)
                comment = await self.game.get_ari_comment('player_bust', 'the player went bust')
                embed.description = comment
                await interaction.edit_original_response(embed=embed, view=None)
                self.game.game_over = True
                if self.game.user_id in active_games:
                    del active_games[self.game.user_id]
            else:
                embed = self.game.create_embed()
                comment = await self.game.get_ari_comment('player_hit', f'drew {card["rank"]}{card["suit"]}')
                embed.description = comment
                await interaction.edit_original_response(embed=embed, view=BlackjackView(self.game))

class StandButton(Button):
    def __init__(self, game):
        super().__init__(label="Stand", style=discord.ButtonStyle.red, custom_id="stand")
        self.game = game
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message("thats not your game bro", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        player_score = self.game.calculate_score(self.game.player_hand)
        dealer_score = self.game.calculate_score(self.game.dealer_hand)
        
        while dealer_score <= DEALER_HIT_LIMIT:
            await asyncio.sleep(1)
            card = self.game.deal_card()
            if card:
                self.game.dealer_hand.append(card)
                dealer_score = self.game.calculate_score(self.game.dealer_hand)
        
        if dealer_score > BLACKJACK:
            game_result = 'dealer_bust'
            payout = self.game.bet * 2
        elif dealer_score > player_score:
            game_result = 'dealer_wins'
            payout = 0
        elif dealer_score < player_score:
            game_result = 'player_wins'
            payout = self.game.bet * 2
        else:
            game_result = 'push'
            payout = self.game.bet
        
        if payout > 0:
            l.add_xp_user(str(interaction.user), payout)
        
        comment = await self.game.get_ari_comment(game_result, f'result: {game_result}')
        
        embed = self.game.create_embed(final=True)
        embed.description = comment
        
        embed.add_field(name="Result", value=f"{game_result.replace('_', ' ').title()} | {payout} XP")
        
        await interaction.edit_original_response(embed=embed, view=None)
        
        self.game.game_over = True
        if self.game.user_id in active_games:
            del active_games[self.game.user_id]

class DoubleDownButton(Button):
    def __init__(self, game):
        super().__init__(label="Double Down", style=discord.ButtonStyle.blurple, custom_id="double")
        self.game = game
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message("thats not your game bro", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        self.game.bet *= 2
        card = self.game.deal_card()
        if card:
            self.game.player_hand.append(card)
            score = self.game.calculate_score(self.game.player_hand)
            
            if score > BLACKJACK:
                embed = self.game.create_embed(bust=True)
                await interaction.edit_original_response(embed=embed, view=None)
                comment = await self.game.get_ari_comment('player_bust', 'player doubled and went bust')
                await interaction.followup.send(comment)
            else:
                dealer_score = self.game.calculate_score(self.game.dealer_hand)
                
                while dealer_score <= DEALER_HIT_LIMIT:
                    await asyncio.sleep(1)
                    card = self.game.deal_card()
                    if card:
                        self.game.dealer_hand.append(card)
                        dealer_score = self.game.calculate_score(self.game.dealer_hand)
                
                embed = self.game.create_embed(final=True)
                
                if dealer_score > BLACKJACK:
                    game_result = 'dealer_bust'
                    payout = self.game.bet * 2
                elif dealer_score > score:
                    game_result = 'dealer_wins'
                    payout = 0
                elif dealer_score < score:
                    game_result = 'player_wins'
                    payout = self.game.bet * 2
                else:
                    game_result = 'push'
                    payout = self.game.bet
                
                if payout > 0:
                    l.add_xp_user(str(interaction.user), payout)
                
                comment = await self.game.get_ari_comment(game_result, f'doubled down, result: {game_result}')
                embed.description = comment
                await interaction.edit_original_response(embed=embed, view=None)
                await interaction.followup.send(f"Result: {game_result.replace('_', ' ').title()} | {payout} XP")
            
            self.game.game_over = True
            if self.game.user_id in active_games:
                del active_games[self.game.user_id]

class SurrenderButton(Button):
    def __init__(self, game):
        super().__init__(label="Surrender", style=discord.ButtonStyle.gray, custom_id="surrender")
        self.game = game
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message("thats not your game bro", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        embed = self.game.create_embed(final=True)
        surrender_comment = await self.game.get_ari_comment('player_surrendered', 'the player gave up')
        embed.description = surrender_comment
        await interaction.edit_original_response(embed=embed, view=None)
        
        returned = self.game.bet // 2
        l.add_xp_user(str(interaction.user), returned)
        
        await interaction.followup.send(f"Surrendered. Returned: {returned} XP")
        
        self.game.game_over = True
        if self.game.user_id in active_games:
            del active_games[self.game.user_id]

async def handle_blackjack_command(message, cxstorage):
    user_id = message.author.id
    
    if user_id in active_games and not active_games[user_id]['game'].game_over:
        await message.reply("you already got a game going. finish it or wait for it to timeout fam")
        return
    
    try:
        bet_amount = int(message.content.replace('!blackjack', '').strip()) if len(message.content.split()) > 1 else 100
    except ValueError:
        bet_amount = 100
    
    if bet_amount < 10:
        await message.reply("minimum bet is 10 xp bro")
        return
    
    user_xp = l.get_xp_user(str(message.author)) or 0
    
    if user_xp < bet_amount:
        await message.reply(f"you only got {user_xp} xp, need {bet_amount} to bet")
        return
    
    l.add_xp_user(str(message.author), -bet_amount)
    
    game = BlackjackGame(user_id, message.author.display_name, str(message.author), message.channel, cxstorage)
    game.bet = bet_amount
    game.start_round()
    
    player_score = game.calculate_score(game.player_hand)
    dealer_first_card = game.dealer_hand[0]
    dealer_showing = f"{dealer_first_card['rank']}{dealer_first_card['suit']}"
    
    if player_score == BLACKJACK:
        dealer_score = game.calculate_score(game.dealer_hand)
        if dealer_score == BLACKJACK:
            game_result = 'push'
            l.add_xp_user(str(message.author), game.bet)
            payout = game.bet
            comment = await game.get_ari_comment('push', 'both have blackjack - push')
        else:
            game_result = 'blackjack'
            payout = int(game.bet * 2.5)
            l.add_xp_user(str(message.author), payout)
            comment = await game.get_ari_comment('blackjack', 'player hit blackjack!')
        
        embed = game.create_embed(final=True)
        embed.description = comment
        embed.add_field(name="Result", value=f"{game_result.replace('_', ' ').title()} | {payout} XP")
        await message.reply(embed=embed, view=None)
        return
    
    active_games[user_id] = {
        'game': game,
        'chat_context': '',
    }
    
    embed = game.create_embed()
    comment = await game.get_ari_comment('initial', f'dealer showing {dealer_showing}')
    embed.description = comment
    
    await message.reply(embed=embed, view=BlackjackView(game))
