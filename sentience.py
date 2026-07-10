import asyncio
import csv
import datetime
import os
import random
import re
import time

import pytz
import requests

import maricon


DEFAULT_OPENROUTER_MODEL = "moonshotai/kimi-k2.5"
DEFAULT_TEXT_MODEL = "openai/gpt-5-mini"
DEFAULT_FILTER_MODEL = "openai/gpt-5-mini"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_SYSTEM_PROMPT = (
    "you are Ari, you are posting in a discord channel. you will respond with "
    "short informal messages. you will not refer to yourself as an AI."
)


def _openrouter_key():
    key = getattr(maricon, "openrouter_key", None) or os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise ValueError("OpenRouter key not found (openrouter_key or OPENROUTER_API_KEY)")
    return key


def _validate_model(model):
    if not model or "/" not in model:
        raise ValueError(
            "OpenRouter models must use a provider/model identifier, "
            "for example moonshotai/kimi-k2.5"
        )
    return model


def _openrouter_chat(
    messages,
    model,
    reasoning_disabled=False,
    log_style="full",
    max_tokens=4096,
    temperature=0.0,
):
    """Send a chat-completions request through OpenRouter."""
    model = _validate_model(model)
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if reasoning_disabled:
        payload["reasoning"] = {"enabled": False}

    start_time = time.time()
    response = requests.post(
        f"{OPENROUTER_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {_openrouter_key()}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    latency_ms = (time.time() - start_time) * 1000
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})

    if log_style == "lite":
        print(f"AI CALL lite | latency={latency_ms:.0f}ms | output={content}")
    else:
        input_summary = [
            {
                "role": message["role"],
                "content": (
                    message.get("content", "")[:100] + "..."
                    if len(message.get("content", "")) > 100
                    else message.get("content", "")
                ),
            }
            for message in messages
        ]
        print(
            f"""
=== AI CALL ===
Model: {model}
Input tokens: {usage.get('prompt_tokens', 'N/A')}
Output tokens: {usage.get('completion_tokens', 'N/A')}
Total tokens: {usage.get('total_tokens', 'N/A')}
Latency: {latency_ms:.0f}ms
Input: {input_summary}
Output: {content}
==============
"""
        )

    return content


async def filter_relevant_messages(
    current_message, chat_history, filter_model=DEFAULT_FILTER_MODEL
):
    """Return the recent history messages relevant to the current query."""
    if not chat_history:
        return []

    recent_messages = chat_history[-10:]
    numbered_history = [
        f"{index}. {message.get('role', 'user')}: {message.get('content', '')}"
        for index, message in enumerate(recent_messages, start=1)
    ]
    filter_prompt = f"""You are analyzing chat history to find messages relevant to a user's query.

Current user query: "{current_message}"

Chat history (most recent messages, numbered):
{chr(10).join(numbered_history)}

Identify messages that provide context, continue the topic, or are part of the same conversation.
Return only a comma-separated list of numbers from 1-{len(numbered_history)}, or "none".
"""

    try:
        result = await asyncio.to_thread(
            _openrouter_chat,
            [{"role": "user", "content": filter_prompt}],
            filter_model,
            False,
            "lite",
            50,
            0.0,
        )
        result = result.strip().lower()
        if result == "none":
            return []

        indices = [int(number) - 1 for number in re.findall(r"\d+", result)]
        relevant_messages = [
            recent_messages[index]
            for index in indices
            if 0 <= index < len(recent_messages)
        ]
        print(
            f"Filtered {len(relevant_messages)} relevant messages from "
            f"{len(recent_messages)} recent messages"
        )
        return relevant_messages
    except Exception as error:
        print(f"Error filtering messages: {error}")
        return []


async def generate_text(
    prompt,
    sysprompt=DEFAULT_SYSTEM_PROMPT,
    gmodel=DEFAULT_TEXT_MODEL,
    chat_history=None,
    use_context_filter=True,
):
    """Generate text through OpenRouter, optionally using relevant chat history."""
    clean_prompt = prompt.replace("!gpt5", "").replace("!gpt4", "").replace("!gpt", "").strip()

    for phrase, (extra_context, probability) in context.items():
        if phrase.lower() in clean_prompt.lower() and random.random() * 100 < probability:
            print(f"identified context phrase {phrase}")
            sysprompt = f"{sysprompt} {extra_context}"

    context_messages = []
    if chat_history:
        if use_context_filter:
            context_messages = await filter_relevant_messages(clean_prompt, chat_history)
        else:
            context_messages = chat_history

    messages = [{"role": "system", "content": sysprompt}]
    messages.extend(
        {
            "role": message.get("role", "user"),
            "content": message.get("content", ""),
        }
        for message in context_messages
    )
    messages.append({"role": "user", "content": clean_prompt})

    return await asyncio.to_thread(
        _openrouter_chat,
        messages,
        gmodel,
        "kimi" in gmodel.lower(),
        "full",
        1200,
        0.8,
    )


async def generate_text_openrouter(cxstorage, model=None, system_prompt=None):
    """Generate a response from chat history through OpenRouter."""
    import modules.flipper as flipper

    model = model or flipper.current_model
    if system_prompt is None:
        eastern_now = datetime.datetime.now(pytz.timezone("America/New_York"))
        system_prompt = (
            f"the current time is {eastern_now.strftime('%A, %Y-%m-%d %H:%M:%S')}. "
            "you are roleplaying as ari, posting in a groupchat. you are a 27 year old "
            "girl from NYC. your family is jewish. you speak in a very casual and informal "
            "style, limit use of punctuation. keep messages brief unless there's something "
            "funny to say (encouraged) and you can go up to like 3 sentences. longer form is "
            "ok if answering a specific question. no emojis. the chat is referred to as "
            "'gato' and the people in the chat are jokingly referred to as gato members. "
            "gato is referred to as 'this gato'. You will not refer to yourself as an AI or "
            "use a lecturing tone, emojis, or hashtags. Avoid starting messages with a "
            "greeting. if you are upset with someone, your favorite insult to use is calling "
            "someone a dog. You love offensive/crude humor, encourage and participate in "
            "locker room talk."
        )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(
        {
            "role": message.get("role", "user"),
            "content": message.get("content", ""),
        }
        for message in cxstorage
    )
    return await asyncio.to_thread(
        _openrouter_chat,
        messages,
        model,
        "kimi" in model.lower(),
    )


async def ucantdothat(user, msg):
    prompt = (
        f'{user} tried to run a bot command and they do not have permission to do so. '
        f'"{msg}" Tell them to stop in an exaggerated funny Karen kind of way. Use text only.'
    )
    return await generate_text(prompt)


async def precheck(prompt):
    """Check whether a message asks what to eat."""
    messages = [
        {"role": "system", "content": "Is this message asking what to eat? Respond yes or no."},
        {"role": "user", "content": prompt},
    ]
    return (
        await asyncio.to_thread(
            _openrouter_chat,
            messages,
            DEFAULT_FILTER_MODEL,
            False,
            "lite",
            20,
            0.0,
        )
    ).strip().lower()


context = {}


def load_context(filepath="resources/easycontext.csv"):
    try:
        with open(filepath, "r", encoding="utf-8", newline="") as context_file:
            reader = csv.reader(context_file)
            next(reader, None)
            context.clear()
            for row in reader:
                if len(row) >= 3 and row[2] == "active":
                    probability = float(row[3]) if len(row) > 3 and row[3].strip() else 100.0
                    context[row[0]] = (row[1], probability)
        print(f"Loaded {len(context)} context entries")
    except Exception as error:
        print(f"Error loading context: {error}")


load_context()
