import openai
import maricon
import personality
import asyncio

openai.api_key = maricon.gptkey

# gpt-3.5-turbo
# text-davinci-002


# Initialize a dictionary to store conversation history for each user
user_conversations = {}
cm_chat_conversations = {}


async def generate_text_with_timeout(prompt, user_id):
    try:
        return await asyncio.wait_for(generate_text(prompt, user_id), timeout=10)
    except asyncio.TimeoutError:
        return "obama"

async def generate_text(prompt,user_id,personality_context=personality.malik):
    # Check if the user already has a conversation history
    if user_id not in user_conversations:
        user_conversations[user_id] = ""

    # Update the conversation history with the new message
    user_conversations[user_id] += f"\nUser {user_id}: {prompt}"

    #full_prompt = f"{personality_context} \n {user_conversations[user_id]}"
    full_prompt = [{"role": "user", "content": f"{personality_context.prompt} \n {user_conversations[user_id]}"}]

    response = openai.ChatCompletion.create(
    model="gpt-4",
    max_tokens=200,
    temperature=1.2,
    messages = full_prompt)

    print(response)
    
    generated_text = response.choices[0].message.content.strip()

    user_conversations[user_id] += f"\nAI: {generated_text}"

    print(f'debug + {user_conversations[user_id]}')

    print('text before replace: ' + generated_text)
    
    if ":" in generated_text:
        generated_text = generated_text[generated_text.find(":")+1:]
    
    generated_text = str(generated_text.replace('AI:',''))
    for name in personality.personality_names:
        #split by space
        for word in name.split(' '):
            generated_text = generated_text.replace(word + ':','')

    # clear user conversation if it has more than 15 ':'s
    # save money!
    if user_conversations[user_id].count(':') > 15:
        user_conversations[user_id] = ""

    return generated_text

async def generate_text_cm(prompt, username, personality_context=personality.ari):
    # Check if the conversation history exists
    if "conversation" not in globals():
        global conversation
        conversation = ""

    # Update the conversation history with the new message
    conversation += f"\n{username}: {prompt}"

    #full_prompt = f"{personality_context} \n {conversation}"
    full_prompt = [{"role": "user", "content": f"{personality_context.prompt} \n {conversation}"}]

    response = openai.ChatCompletion.create(
    model="gpt-4",
    max_tokens=200,
    temperature=1.2,
    messages = full_prompt)

    print(response)
    
    generated_text = response.choices[0].message.content.strip()

    conversation += f"\nAI: {generated_text}"

    print(f'debug + {conversation}')

    print('text before replace: ' + generated_text)
    
    if ":" in generated_text:
        generated_text = generated_text[generated_text.find(":")+1:]
    
    generated_text = str(generated_text.replace('AI:',''))
    for name in personality.personality_names:
        #split by space
        for word in name.split(' '):
            generated_text = generated_text.replace(word + ':','')

    # replace words in generated text with gato slang
    for word in generated_text.split(' '):
        if word in gato_slang:
            generated_text = generated_text.replace(word, gato_slang[word])

    # clear conversation if it has more than 15 ':'s
    # save money!
    if conversation.count(':') > 15:
        conversation = ""

    return generated_text

async def generate_text_with_timeout_cm(prompt, user_id, personality_context):
    try:
        return await asyncio.wait_for(generate_text_cm(prompt, user_id, personality_context), timeout=15)
    except asyncio.TimeoutError:
        return "obama"
    
async def generate_text_with_timeout_gpt(prompt):
    try:
        return await asyncio.wait_for(generate_text_gpt(prompt), timeout=15)
    except asyncio.TimeoutError:
        return "obama"
    
#basic gpt
async def generate_text_gpt(prompt):

    prompt = prompt.replace('!gpt','')

    full_prompt = [{"role": "user", "content": f"{prompt}"}]

    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    max_tokens=1200,
    temperature=.8,
    messages = full_prompt)

    print(response)
    
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