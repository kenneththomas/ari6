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


# Project-defined model registry. Keep model selection here rather than in the
# environment so upgrades are explicit and version-controlled.
DEFAULT_OPENROUTER_MODEL = "moonshotai/kimi-k2.5"
DEFAULT_TEXT_MODEL = "openai/gpt-5.4-mini"
DEFAULT_FILTER_MODEL = "openai/gpt-5.4-mini"
DEEPSEEK_MODEL = "deepseek/deepseek-v4-pro"
GOOGLE_MODEL = "google/gemini-3.5-flash"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_MAX_ATTEMPTS = 3
OPENROUTER_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
MISSING_API_KEY_MESSAGE = "No API key found."
# Log prompts and model output by default. Set this to False to retain only
# model, token, and latency metadata for all calls.
LOG_AI_CONTENT = True
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


class OpenRouterResponseError(RuntimeError):
    """Raised when OpenRouter returns a successful but malformed response."""


def _retry_delay(response, attempt):
    retry_after = response.headers.get("Retry-After", "") if response is not None else ""
    try:
        return min(max(0.0, float(retry_after)), 5.0)
    except (TypeError, ValueError):
        return min(0.5 * (2 ** (attempt - 1)), 2.0)


def _loggable_messages(messages):
    """Return messages suitable for logs without embedded base64 image data."""
    loggable = []
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, list):
            content_parts = []
            for part in content:
                if part.get("type") == "image_url":
                    content_parts.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": "[image data omitted]"},
                        }
                    )
                else:
                    content_parts.append(part)
            content = content_parts
        loggable.append({"role": message.get("role", "unknown"), "content": content})
    return loggable


def openrouter_chat(
    messages,
    model,
    reasoning_disabled=False,
    log_style="full",
    max_tokens=4096,
    temperature=0.0,
    timeout=120,
    log_content=None,
):
    """Send a chat-completions request through OpenRouter."""
    model = _validate_model(model)
    try:
        api_key = _openrouter_key()
    except ValueError:
        return MISSING_API_KEY_MESSAGE

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if reasoning_disabled:
        payload["reasoning"] = {"enabled": False}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    start_time = time.time()

    response = None
    for attempt in range(1, OPENROUTER_MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout,
            )
        except (requests.ConnectionError, requests.Timeout):
            if attempt == OPENROUTER_MAX_ATTEMPTS:
                raise
            delay = _retry_delay(None, attempt)
            print(f"OpenRouter request failed; retrying in {delay:.1f}s")
            time.sleep(delay)
            continue

        if (
            response.status_code in OPENROUTER_RETRYABLE_STATUS_CODES
            and attempt < OPENROUTER_MAX_ATTEMPTS
        ):
            delay = _retry_delay(response, attempt)
            print(
                f"OpenRouter returned {response.status_code}; "
                f"retrying in {delay:.1f}s"
            )
            time.sleep(delay)
            continue

        response.raise_for_status()
        break

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise OpenRouterResponseError(
            "OpenRouter returned a response without message content"
        ) from error

    if not isinstance(content, str):
        raise OpenRouterResponseError("OpenRouter message content was not text")

    latency_ms = (time.time() - start_time) * 1000
    usage = data.get("usage", {})
    if not isinstance(usage, dict):
        usage = {}
    if log_content is None:
        log_content = LOG_AI_CONTENT

    if log_style == "lite":
        log_line = (
            f"AI CALL lite | model={model} | latency={latency_ms:.0f}ms | "
            f"tokens={usage.get('total_tokens', 'N/A')}"
        )
        if log_content:
            log_line += f" | output={content}"
        print(log_line)
    elif log_style == "full":
        content_log = ""
        if log_content:
            content_log = (
                f"Input: {_loggable_messages(messages)}\n"
                f"Output: {content}\n"
            )
        print(
            f"""
=== AI CALL ===
Model: {model}
Input tokens: {usage.get('prompt_tokens', 'N/A')}
Output tokens: {usage.get('completion_tokens', 'N/A')}
Total tokens: {usage.get('total_tokens', 'N/A')}
Latency: {latency_ms:.0f}ms
{content_log}==============
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
            openrouter_chat,
            messages=[{"role": "user", "content": filter_prompt}],
            model=filter_model,
            reasoning_disabled=True,
            log_style="lite",
            max_tokens=50,
            temperature=0.0,
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
        openrouter_chat,
        messages=messages,
        model=gmodel,
        reasoning_disabled=True,
        log_style="full",
        max_tokens=1200,
        temperature=0.8,
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
        openrouter_chat,
        messages=messages,
        model=model,
        reasoning_disabled="kimi" in model.lower(),
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
            openrouter_chat,
            messages=messages,
            model=DEFAULT_FILTER_MODEL,
            reasoning_disabled=True,
            log_style="lite",
            max_tokens=20,
            temperature=0.0,
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
