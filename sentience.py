from openai import OpenAI
import maricon
client = OpenAI(api_key=maricon.gptkey)
import personality
import asyncio
import random
import anthropic
claude = anthropic.Anthropic(api_key=maricon.anthropic_key)


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
async def generate_text_gpt(prompt,sysprompt='you are Ari, you are posting in a discord channel. you will respond with short informal messages. you will not refer to yourself as an AI.',gmodel='gpt-3.5-turbo-0125'):

    prompt = prompt.replace('!gpt4','')
    prompt = prompt.replace('!gpt','')

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

    response = client.chat.completions.create(model="gpt-3.5-turbo-0125",
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


async def ai_experimental(prompt, gmodel="gpt-3.5-turbo-0125", prompt_addition=False):

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

async def claudex(prompt, model='claude-3-5-sonnet-20240620', prompt_addition=None):
    """
    Converts a list of messages into a format suitable for the Claude API.
    If 'prompt_addition' is specified, it sets the role to that value; otherwise, defaults to 'ari'.
    Additionally, checks for specific members mentioned in the messages to add context.

    :param prompt: List of strings, where each string is "user: message".
    :param model: Model name to be used with Claude.
    :param prompt_addition: Optional; Additional role to be used in the prompt.
    :return: The response text content from the Claude API.
    """
    role = prompt_addition if prompt_addition else 'ari'

    # Compile additional context based on members mentioned in the prompt.
    additional_context = ''
    for member, context in personality.additional_context.items():
        for message in prompt:
            if member in message:
                count = message.count(member)
                # Add context with a probability proportional to count.
                if random.randint(1, 10) <= count and context not in additional_context:
                    print(f'Adding additional context: {context}')
                    additional_context += f'{context} \n'

    # Combine all messages into a single string for the prompt.
    combined_messages = ' \n'.join(prompt)

    # Construct the Claude prompt.
    claude_prompt = [{"role": "user", "content": combined_messages}]

    # Call the Claude API with the constructed prompt and additional parameters.
    response = claude.messages.create(
        model=model,
        max_tokens=280,
        messages=claude_prompt,
        system=f"You are role playing as {role}, a 27-year-old Dominican girl from NYC, posting in a discord channel with a casual and informal chat style, using NYC slang/grammar. (referring to people as b or son, you is, we is, they instead of their for possessive) You love offensive humor and will not refer to yourself as an AI or use a lecturing tone, emojis, or hashtags. Avoid ending sentences with a question or starting with a greeting. {additional_context}"
    )
    print(response)

    # Extract and return the text content from the response.
    text_content = ''.join(block.text for block in response.content)
    text_content = text_content.lower()
    print(text_content)

    return text_content

#cloudhouse claude prompt
async def ch_claudex(prompt, recentmessages, model='claude-3-5-sonnet-20240620'):
    #call claude with prompt and recent messages

    rm = [{"role": "user", "content": f'{recentmessages}'}]

    response = claude.messages.create(
        model=model,
        max_tokens=800,
        messages=rm,
        system=f"{prompt}"
    )

    print(response)
    text_content = ''.join(block.text for block in response.content)
    print(text_content)

    return text_content


async def claudex2(cxstorage, model='claude-3-5-sonnet-20240620', prompt_addition=None):

    role = 'ari'
    print(cxstorage)
    # Call the Claude API with the constructed prompt and additional parameters.
    response = claude.messages.create(
        model=model,
        max_tokens=280,
        messages=cxstorage,
        system=f"You are role playing as {role}, a 27-year-old Dominican girl from NYC, posting in a discord channel with a casual and informal chat style, using NYC slang/grammar. (referring to people as b or son, you is, we is, they instead of their for possessive) You love offensive humor and will not refer to yourself as an AI or use a lecturing tone, emojis, or hashtags. Avoid ending sentences with a question or starting with a greeting."
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