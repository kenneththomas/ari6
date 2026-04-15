from openai import OpenAI
import maricon
client = OpenAI(api_key=maricon.gptkey)
import personality
import asyncio
import random
import re
import csv
import time
import datetime
import pytz
import requests


translate_language = 'spanish'

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


async def check_if_talking_about_tk(message_content):
    try:
        prompt = f"""You are a classifier that determines if a message is talking about a specific person named "TK".

Rules:
- Only return "True" if the message is clearly talking about a PERSON named TK
- Return "False" if:
  - "tk" appears but refers to something else (like "thank you", "tank", "ticket", etc.)
  - "tk" is part of a word or phrase that's not a person's name
  - The message is just mentioning the word "tk" without context about a person
  - It's unclear if TK refers to a person

Examples:
- "i miss tk" → True (clearly about a person)
- "tk was here earlier" → True (about a person)
- "thank you" → False (not about a person named TK)
- "i have a ticket" → False (not about a person)
- "tk is short for thank you" → False (explaining abbreviation, not about a person)
- "tk" → False (just the word, no context)

Message: "{message_content}"

Return only "True" or "False":"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.0
        )

        result = response.choices[0].message.content.strip().lower()
        return result == "true"

    except Exception as e:
        print(f"Error checking if talking about TK: {e}")
        return False