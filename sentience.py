from openai import OpenAI
import maricon
client = OpenAI(api_key=maricon.gptkey)
import csv
import time

async def generate_text_gpt(prompt, sysprompt='you are Ari, you are posting in a discord channel. you will respond with short informal messages. you will not refer to yourself as an AI.', gmodel='gpt-4o-mini'):

    prompt = prompt.replace('!gpt4', '')
    prompt = prompt.replace('!gpt', '')

    processed_phrases = set()
    prompt_lower = prompt.lower()

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

    generated_text = response.choices[0].message.content.strip()
    generated_text = generated_text.lower()

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

async def ucantdothat(user, msg):
    prompt = f'{user} tried to run a bot command and they do not have permission to do so. "{msg}" and tell them to stop but in like a exaggerated funny karen kind of way. use text only.'
    return await generate_text_gpt(prompt)


context = {}

def load_context(filepath: str = 'resources/easycontext.csv') -> None:
    try:
        with open(filepath, 'r') as file:
            reader = csv.reader(file)
            next(reader)
            context.clear()
            for row in reader:
                if row[2] == 'active':
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
