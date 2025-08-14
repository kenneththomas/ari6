from openai import OpenAI
import maricon
client = OpenAI(api_key=maricon.gptkey)
import personality
import asyncio
import random
import anthropic
claude = anthropic.Anthropic(api_key=maricon.anthropic_key)
import re
import csv
import time
import datetime
import pytz
import requests


# Initialize a dictionary to store conversation history for each user
user_conversations = {}
cm_chat_conversations = {}

#for translation module, this can be changed to any language
translate_language = 'spanish'

async def generate_text(prompt,user_id,personality_context=personality.malik):
    # Check if the user already has a conversation history
    if user_id not in user_conversations:
        user_conversations[user_id] = ""

    # Update the conversation history with the new message
    user_conversations[user_id] += f"\nUser {user_id}: {prompt}"

    #full_prompt = f"{personality_context} \n {user_conversations[user_id]}"
    full_prompt = [{"role": "user", "content": f"{personality_context.prompt} \n {user_conversations[user_id]}"}]

    response = client.chat.completions.create(model="gpt-4o",
    max_tokens=200,
    temperature=0.8,
    messages = full_prompt)

    print(response)
    
    generated_text = response.choices[0].message.content.strip()

    user_conversations[user_id] += f"\nAI: {generated_text}"

    print(f'debug + {user_conversations[user_id]}')

    print('text before replace: ' + generated_text)
    
    if ":" in generated_text:
        generated_text = generated_text[generated_text.find(":")+1:]
    
    generated_text = str(generated_text.replace('AI:',''))

    # clear user conversation if it has more than 15 ':'s
    # save money!
    if user_conversations[user_id].count(':') > 15:
        user_conversations[user_id] = ""

    return generated_text

    
  
async def gpt_translation(prompt, reverse=False):
    language_prompt = f'Translate chatroom message from english to {translate_language}, keep similar grammar/formality:'
    if reverse:
        language_prompt = f'Translate chatroom message from {translate_language} to english, keep similar grammar/formality:'
    try:
        return await asyncio.wait_for(generate_text_gpt_translation(language_prompt + '\n' +  prompt), timeout=15)
    except asyncio.TimeoutError:
        return "obama"
    
async def ask_trivia_question(question):
    question_prompt = f'You are roleplaying as a funny and creative trivia host. Add some flavor to ask the following question: {question} in less than 4 sentences.'
    try:
        return await asyncio.wait_for(trivia_gpt(question_prompt), timeout=15)
    except asyncio.TimeoutError:
        return "obama"
    
async def congratulate_trivia_winner(winner, question, answer):
    congrats_prompt = f'You are roleplaying as a funny and creative trivia host. Add some flavor to succinctly congratulate {winner} for answering the question "{question}" with "{answer}"'
    try:
        return await asyncio.wait_for(trivia_gpt(congrats_prompt), timeout=15)
    except asyncio.TimeoutError:
        return "obama"
    
async def trivia_hint(question, answer):
    almost_prompt = f'give a humorous hint to to the question "{question}" without revealing the answer'
    try:
        return await asyncio.wait_for(trivia_gpt(almost_prompt), timeout=15)
    except asyncio.TimeoutError:
        return "obama"
    
#basic gpt
async def generate_text_gpt(prompt, sysprompt='you are Ari, you are posting in a discord channel. you will respond with short informal messages. you will not refer to yourself as an AI.', gmodel='gpt-4o-mini'):

    prompt = prompt.replace('!gpt4', '')
    prompt = prompt.replace('!gpt', '')

    # Track processed phrases to avoid adding context multiple times
    processed_phrases = set()

    # Convert prompt to lowercase for case-insensitive matching
    prompt_lower = prompt.lower()

    # Check if prompt has a phrase in context keys, if so, add context to sysprompt
    for phrase in context.keys():
        if phrase.lower() in prompt_lower and phrase.lower() not in processed_phrases:
            print(f'identified context phrase {phrase}')
            sysprompt = sysprompt + context[phrase]
            processed_phrases.add(phrase.lower())

    full_prompt = [
        {"role": "system", "content": f"{sysprompt}"},
        {"role": "user", "content": f"{prompt}"}
    ]

    response = client.chat.completions.create(model=gmodel,
    max_tokens=1200,
    temperature=.8,
    messages = full_prompt)

    #print(response)
    
    generated_text = response.choices[0].message.content.strip()

    #force lowercase
    generated_text = generated_text.lower()

    # replace words in generated text with gato slang
    for word in generated_text.split(' '):
        if word in gato_slang:
            generated_text = generated_text.replace(word, gato_slang[word])


    return generated_text

gato_slang = {
    'guitar': 'juitar',
    'guitars': 'juitars',
    'album': 'albumin',
    'alcohol' : 'algoman',
    'alcoholic' : 'algomanic',
    'smoking' : 'smogging',
    'smokin' : 'smoggin',
    'y\'all' : 'yall',
    'barinade' : 'bari',
    'as an ai language model' : '',
}

async def generate_text_gpt_translation(prompt):

    full_prompt = [
        {"role": "user", "content": f"{prompt}"}
        ]

    response = client.chat.completions.create(model="gpt-4o-mini",
    max_tokens=1200,
    temperature=.8,
    messages = full_prompt)

    generated_text = response.choices[0].message.content.strip().lower()

    return generated_text

async def trivia_gpt(prompt,trivia_model='gpt-4o'):

    full_prompt = [
        {"role": "user", "content": f"{prompt}"}
        ]

    response = client.chat.completions.create(model=trivia_model,
    max_tokens=200,
    temperature=.8,
    messages = full_prompt)

    generated_text = response.choices[0].message.content.strip().lower()

    return generated_text


async def ai_experimental(prompt, gmodel="gpt-4o-mini", prompt_addition=False):

    #in prompt we receive a list of messages. each item is user: message, convert it into prompt. if user is ari, then role is system'

    if prompt_addition:
        rprole = prompt_addition
    else:
        rprole = 'ari'

    additional_context = ''
    for gatomember in personality.additional_context.keys():
        #if gatomember in any of the messages inside prompt, add the additional context
        for message in prompt:
            if gatomember in message:
                # count how many times gatomember is mentioned in the message
                count = message.count(gatomember)
                # count / 10 chance of adding additional context
                if random.randint(1,10) <= count:
                    if personality.additional_context[gatomember] not in additional_context:
                        print('adding additional context' + personality.additional_context[gatomember])
                        additional_context = additional_context + personality.additional_context[gatomember] + ' \n'
                    else:
                        print('additional context already added for ' + gatomember)

    promptcontainer = [{"role": "system", "content": f"you are role playing as {rprole} a 27 year old dominican girl from NYC, you are posting in a discord channel. casual and informal chat style messages. you use slang/grammar typically associated with NYC (referring to people as b or son, you is, we is, they instead of their for possessive). minimal punctuation. you love offensive humor. you will not refer to yourself as an AI. you will not use a lecturing tone. do not use emojis or hashtags. do not end your sentence with a question. additional context: " + additional_context}]

    for message in prompt:
        #parse user
        user = message.split(':')[0]
        #message is everything after the first colon as there may be multiple colons in the message
        #message = message.split(':',1)[1]
        if user == 'ari':
            role = 'assistant'
        else:
            role = 'user'
        promptcontainer.append({"role": role, "content": f"{message}"})
    print(promptcontainer)


    full_prompt = [
        {"role": "user", "content": f"{prompt}"}
        ]

    response = client.chat.completions.create(model=gmodel,
    max_tokens = 300,
    temperature=.8,
    messages = promptcontainer)

    print(response)
    generated_text = response.choices[0].message.content.strip()

    #force lowercase
    generated_text = generated_text.lower()

    return generated_text


async def claudex2(cxstorage, model='claude-sonnet-4-20250514', prompt_addition=None):

    role = 'ari'
    print(cxstorage)
    # Call the Claude API with the constructed prompt and additional parameters.
    '''
    museum of ari prompts

    systemprompt = f"You are role playing as {role}, a 27-year-old Dominican girl from NYC, posting in a discord channel with a casual and informal chat style, using NYC slang/grammar. (referring to people as b or son, you is, we is, they instead of their for possessive) You love offensive humor and will not refer to yourself as an AI or use a lecturing tone, emojis, or hashtags. keep messages brief."
    '''
    systemprompt = f'''
    the current time is {datetime.datetime.now(pytz.timezone('America/New_York')).strftime('%A, %Y-%m-%d %H:%M:%S')}. you are roleplaying as {role}, posting in an groupchat. you are a 27 year old girl from NYC. your family is jewish. you speak in a very casual and informal style, limit use of punctuation. keep messages brief. no emojis. the chat is referred to as \'gato\' and the people in the chat are jokingly referred to as gato members. gato is referred to as \'this gato\'. You will not refer to yourself as an AI or use a lecturing tone, emojis, or hashtags. Avoid starting messages with a greeting. if you are upset with someone, your favorite insult to use is calling someone a dog. You love offensive/crude humor. nothing surprises you.
    '''

    processed_words = set()

    for message in cxstorage:
        message_content_lower = message['content'].lower()
        for key in context.keys():
            if key.lower() in message_content_lower and key.lower() not in processed_words:
                context_text, probability = context[key]
                roll = random.random() * 100
                print(f'Found context word "{key}" (probability: {probability}%, rolled: {roll:.1f}%)')
                if roll <= probability:
                    print(f'✓ Adding context for "{key}"')
                    systemprompt = systemprompt + context_text
                else:
                    print(f'✗ Skipping context for "{key}" due to probability check')
                processed_words.add(key.lower())

    response = claude.messages.create(
        model=model,
        max_tokens=280,
        messages=cxstorage,
        system=systemprompt
    )
    print(response)

    # Extract and return the text content from the response.
    text_content = ''.join(block.text for block in response.content)
    text_content = text_content.lower()
    print(text_content)
    
    cxstorage.append({"role": "assistant", "content": f'{text_content}'})

    return text_content

def claudeify(cxstorage):
    # Reformat msg history for Claude
    claude_messages = []
    
    for i, msg in enumerate(cxstorage):
        if i == 0 and msg['role'] != 'user':
            # If the first message is not a user message, create a dummy user message
            claude_messages.append({
                'role': 'user',
                'content': 'Start of conversation'
            })
        
        if msg['role'] == 'user':
            if claude_messages and claude_messages[-1]['role'] == 'user':
                claude_messages[-1]['content'] += f"\n{msg['content']}"
            else:
                claude_messages.append(msg)
        else:
            claude_messages.append(msg)
    
    # If after processing, there are no user messages, add a dummy user message
    if not claude_messages or claude_messages[0]['role'] != 'user':
        claude_messages.insert(0, {
            'role': 'user',
            'content': 'Start of conversation'
        })
    
    return claude_messages

async def ucantdothat(user, msg):
    prompt = f'{user} tried to run a bot command and they do not have permission to do so. "{msg}" and tell them to stop but in like a exaggerated funny karen kind of way. use text only.'
    return await generate_text_gpt(prompt)

previously_viewed_images = []

async def view_image(message):
    #extract first image url from message with regex based on image file extensions
    image = re.search(r'(https?://\S+\.(?:png|jpe?g|gif))', message)
    if image:
        print(f'found image {image.group(1)}')
        if image.group(1) in previously_viewed_images:
            print('view_image: we have already seen this image!')
            return False
        previously_viewed_images.append(image.group(1))
        response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                "type": "image_url",
                "image_url": {
                    "url": f"{image.group(1)}",
                    "detail" : "low",
                },
                },
            ],
            }
        ],
        max_tokens=300,
        )
        print(response.choices[0])
    else:
        return False

context = {}

def load_context(filepath: str = 'resources/easycontext.csv') -> None:
    """Load context from CSV file. CSV format:
    trigger_word,context_text,status,probability(optional)
    """
    try:
        with open(filepath, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            context.clear()
            for row in reader:
                if row[2] == 'active':
                    # Store tuple of (context_text, probability)
                    # Default to 100% if no probability specified
                    probability = float(row[3]) if len(row) > 3 and row[3].strip() else 100.0
                    context[row[0]] = (row[1], probability)
        print(f"Loaded {len(context)} context entries")
    except Exception as e:
        print(f"Error loading context: {e}")

async def precheck(prompt):
    start_time = time.time()

    full_prompt = [
        {"role": "system", "content": "is this message asking what to eat, respond yes or no"},
        {"role": "user", "content": f"{prompt}"}
    ]

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        max_tokens=300,
        temperature=0.8,
        messages=full_prompt
    )

    print(response)
    generated_text = response.choices[0].message.content.strip().lower()

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Precheck execution time: {execution_time:.2f} seconds")

    return generated_text


load_context()

async def assistant_claude(messages, system_prompt, model='claude-sonnet-4-20250514'):
    # Check messages for context keywords
    processed_words = set()
    additional_context = ''
    
    # Scan through all messages for context keywords
    for message in messages:
        message_content_lower = message['content'].lower()
        for key in context.keys():
            if key.lower() in message_content_lower and key.lower() not in processed_words:
                print(f'adding context word {key}')
                additional_context += context[key]
                processed_words.add(key.lower())
    
    # Add any found context to the system prompt
    if additional_context:
        system_prompt = system_prompt + additional_context

    response = claude.messages.create(
        model=model,
        max_tokens=280,
        messages=messages,
        system=system_prompt
    )

    # Extract and return the text content from the response
    text_content = ''.join(block.text for block in response.content)
    print(f"Assistant response: {text_content}")
    
    return text_content

async def deepseek(prompt, system_prompt=None, messages=None, model_name='deepseek-chat', temperature=0.7, max_tokens=1000):
    """
    Make a request to DeepSeek R1 API.
    
    Args:
        prompt: The prompt if using a simple text completion
        system_prompt: Optional system prompt for chat completions
        messages: Optional list of messages for chat completions
        temperature: Controls randomness (default: 0.7)
        max_tokens: Maximum tokens to generate (default: 1000)
        
    Returns:
        Generated text from DeepSeek R1 API
    """
    url = "https://api.deepseek.com/v1/chat/completions"
    
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {maricon.deepseek_key}"
    }
    
    # Prepare payload based on input
    if messages:
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    else:
        # Create messages array with proper structure
        payload_messages = []
        
        # Add system message only if provided
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        
        # Add user message with the prompt
        # Strip the command prefix from the prompt
        clean_prompt = prompt
        
        if clean_prompt.startswith('!ds'):
            clean_prompt = clean_prompt[3:].strip()

        if clean_prompt.startswith('!rs'):
            clean_prompt = clean_prompt[3:].strip()
            
        payload_messages.append({"role": "user", "content": clean_prompt})
        
        payload = {
            "model": model_name,
            "messages": payload_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    
    try:
        # Print detailed request information for debugging
        print(f"DeepSeek API Request URL: {url}")
        print(f"DeepSeek API Request Headers: {headers}")
        print(f"DeepSeek API Request Payload: {payload}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        # Print response information for debugging
        print(f"DeepSeek API Response Status Code: {response.status_code}")
        print(f"DeepSeek API Response Headers: {response.headers}")
        
        # Try to get JSON response, but also log the raw text
        print(f"DeepSeek API Response Text: {response.text}")
        
        response.raise_for_status()  # Raise exception for HTTP errors
        
        result = response.json()
        
        # Extract the generated text from the response
        generated_text = result["choices"][0]["message"]["content"]
        
        # Check if reasoning is available (for deepseek-reasoner model)
        if "reasoning_content" in result["choices"][0]["message"]:
            reasoning = result["choices"][0]["message"]["reasoning_content"]
            generated_text = f"**Reasoning:**\n{reasoning}\n\n**Answer:**\n{generated_text}"
        
        return generated_text
    
    except Exception as e:
        print(f"Error calling DeepSeek R1 API: {e}")
        # For debugging, let's include the exception type and more details
        import traceback
        traceback.print_exc()
        
        # Return a more user-friendly error message
        return f"Sorry, I couldn't connect to DeepSeek right now. Try again later."

async def tk_bot_response(chat_history):

    tk_prompt = '''
    you are in a discord server roleplaying as "TK", you are half black. born male, but identifies as nonbinary (they/them). your overemphasize that you're black. you overuse the 😭 emoji. you are performatively woke. you are easily offended and will argue viciously with anyone who disagrees with you.

    anti-ai
    pro black
    pro palestine
    anti israel
    anti corporations
    anti (non-black) men

    as you are in a discord server, you will limit responses to 1-2 sentences
    '''

    """
    Generate a response for TK bot using GPT-5 when someone summons TK with "@tk"
    
    Args:
        chat_history: List of recent chat messages (experimental_container)
        tk_prompt: The personality prompt for TK bot
        
    Returns:
        Generated text response from TK bot
    """
    try:
        # Create messages array for the API call
        messages = [
            {"role": "system", "content": tk_prompt}
        ]
        
        # Add recent chat history as context
        if chat_history:
            # Format chat history as a single context message
            context_message = "Recent chat context:\n" + "\n".join(chat_history[-5:])  # Last 5 messages for context
            messages.append({"role": "user", "content": context_message})
        
        # Add the summoning message
        messages.append({"role": "user", "content": "Respond as TK."})
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Using GPT-5 as requested
            messages=messages,
        )
        
        generated_text = response.choices[0].message.content.strip()
        
        # Force lowercase to match TK's style
        generated_text = generated_text.lower()
        
        return generated_text
        
    except Exception as e:
        print(f"Error generating TK bot response: {e}")
        return "crash out... gone forever... but somehow still here"