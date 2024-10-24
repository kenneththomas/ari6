import uuid
import random
import lumberjack as l
import control as ct
import sentience
from . import joey  # Changed this line to use relative import

class TriviaHandler:
    def __init__(self):
        self.trivia_question = ''
        self.trivia_answer = ''

    async def handle_trivia_command(self, message):
        self.trivia_question = random.choice(list(l.trivia_questions.keys()))
        self.trivia_answer = l.trivia_questions[self.trivia_question]
        async with message.channel.typing():
            host_question = await sentience.ask_trivia_question(self.trivia_question)
            await message.channel.send(host_question)

    async def handle_trivia_hint(self, message):
        if self.trivia_answer:
            hint = await sentience.trivia_hint(self.trivia_question, self.trivia_answer)
            await message.channel.send(hint)

    async def check_trivia_answer(self, message):
        if self.trivia_answer and message.content.lower() == self.trivia_answer.lower():
            correct_answer = self.trivia_answer
            self.trivia_answer = ''  # Reset answer after correct guess
            l.add_xp_user(str(message.author), 3)
            async with message.channel.typing():
                congratulatory_msg = await sentience.congratulate_trivia_winner(
                    str(message.author), self.trivia_question, correct_answer
                )
                await message.channel.send(congratulatory_msg)

    async def add_trivia_question(self, message):
        new_trivia = message.content.replace('!addquestion', '').strip()
        if ',' not in new_trivia:
            await message.channel.send('Invalid format, use !addquestion question,answer')
            return
            
        question, answer = [item.strip() for item in new_trivia.split(',', 1)]
        question_id = str(uuid.uuid4())[:5]
        
        l.trivia_questions[question] = answer
        l.newquestion[question_id] = [question, answer]
        await message.channel.send(
            f'Added {question} to trivia questions.\n'
            f'breez can save this question with !savequestion {question_id}'
        )

    async def save_trivia_question(self, message):
        if not ct.admincheck(str(message.author)):
            cantdothat = await sentience.ucantdothat(message.author, message.content)
            await message.reply(cantdothat)
            return
            
        question_id = message.content.replace('!savequestion', '').strip()
        if question_id in l.newquestion:
            question, answer = l.newquestion[question_id]
            l.questions_to_save[question] = answer
            await message.channel.send(f'Saved {question} to trivia questions')
        else:
            await message.channel.send(f'{question_id} not found')

    async def show_help(self, message):
        await message.channel.send(joey.help_message)
