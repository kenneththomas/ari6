import asyncio
import csv
import datetime
import os
import random
import re
import time

import requests

import maricon
from modules.personas import persona_store


# Project-defined model registry. Keep model selection here rather than in the
# environment so upgrades are explicit and version-controlled.
DEFAULT_OPENROUTER_MODEL = "moonshotai/kimi-k2.5"
DEFAULT_TEXT_MODEL = "openai/gpt-5.4-mini"
DEFAULT_FILTER_MODEL = "openai/gpt-5.4-mini"
DEEPSEEK_MODEL = "deepseek/deepseek-v4-pro"
GOOGLE_MODEL = "google/gemini-3.5-flash"
INFORMATIVE_MAX_TOKENS = 2400
REPLY_ROUTE_CHAT = "chat"
REPLY_ROUTE_SEARCH = "search"
WEB_SEARCH_TOOL = {
    "type": "openrouter:web_search",
    "parameters": {
        "search_context_size": "low",
        "max_total_results": 5,
    },
}
WEB_SEARCH_MODE_PROMPT = """\
Web search mode is active. You must use the available web search tool before
answering. Ground factual claims in the retrieved results and include source
links. If the search results do not verify the requested information, say so
instead of filling gaps from memory.
"""
REPLY_ROUTE_PROMPT = """\
Classify whether replying to the latest message requires searching the public web.
Return exactly one word: search or chat.

Return search when the user explicitly asks to search, browse, look something up,
verify a claim, or provide sources; or when a reliable answer depends on current,
recent, live, changing, or externally verifiable information such as news, scores,
weather, prices, schedules, office holders, laws, or current software versions.

Return chat for casual conversation, creative requests, opinions, jokes, and
timeless knowledge. A request being detailed or substantial does not by itself
require search. Use the recent conversation only to resolve follow-up references.
"""
INFORMATIVE_MODE_PROMPT = """\
Informative mode is active for this !gpt request. Prioritize a useful, accurate,
and self-contained answer over group-chat brevity. Explain the subject clearly,
include necessary context, and give step-by-step instructions, examples, caveats,
or practical next actions when they help. Use paragraphs, bullets, headings, and
code blocks when they improve readability. Adapt the length to the question and
do not pad a simple answer, but do not apply the persona's usual sentence limit
or preference for short chat messages. Keep only a light touch of Ari's casual
voice; clarity and instruction come first.
"""
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_MAX_ATTEMPTS = 3
OPENROUTER_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
MISSING_API_KEY_MESSAGE = "No API key found."
# Log prompts and model output by default. Set this to False to retain only
# model, token, and latency metadata for all calls.
LOG_AI_CONTENT = True
AI_METADATA_LOGGER = None


def set_ai_metadata_logger(logger):
    """Configure a best-effort sink for metadata-only AI call records."""
    global AI_METADATA_LOGGER
    AI_METADATA_LOGGER = logger


def _log_ai_metadata(**metadata):
    if AI_METADATA_LOGGER is None:
        return
    try:
        AI_METADATA_LOGGER(**metadata)
    except Exception as error:
        # Telemetry must never turn a successful AI request into a bot failure.
        print(f"Could not persist AI call metadata: {error}")


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
    purpose=None,
    tools=None,
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
    if tools:
        payload["tools"] = tools

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    start_time = time.time()

    response = None
    attempt = 0

    def record_metadata(
        success,
        usage=None,
        error_type=None,
        web_search_requests=None,
        citation_urls=None,
    ):
        usage = usage if isinstance(usage, dict) else {}
        citation_urls = citation_urls or []
        _log_ai_metadata(
            provider="openrouter",
            model=model,
            purpose=purpose,
            input_tokens=usage.get("prompt_tokens", usage.get("input_tokens")),
            output_tokens=usage.get("completion_tokens", usage.get("output_tokens")),
            total_tokens=usage.get("total_tokens"),
            latency_ms=(time.time() - start_time) * 1000,
            attempt_count=attempt,
            success=success,
            status_code=getattr(response, "status_code", None),
            error_type=error_type,
            cost=usage.get("cost"),
            web_search_requests=web_search_requests,
            citation_count=len(citation_urls),
            citation_urls=citation_urls,
        )

    for attempt in range(1, OPENROUTER_MAX_ATTEMPTS + 1):
        response = None
        try:
            response = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout,
            )
        except (requests.ConnectionError, requests.Timeout) as error:
            if attempt == OPENROUTER_MAX_ATTEMPTS:
                record_metadata(False, error_type=type(error).__name__)
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

        try:
            response.raise_for_status()
        except requests.RequestException as error:
            record_metadata(False, error_type=type(error).__name__)
            raise
        break

    try:
        data = response.json()
        response_message = data["choices"][0]["message"]
        content = response_message["content"]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        record_metadata(False, error_type="OpenRouterResponseError")
        raise OpenRouterResponseError(
            "OpenRouter returned a response without message content"
        ) from error

    if not isinstance(content, str):
        record_metadata(False, error_type="OpenRouterResponseError")
        raise OpenRouterResponseError("OpenRouter message content was not text")

    latency_ms = (time.time() - start_time) * 1000
    usage = data.get("usage", {})
    if not isinstance(usage, dict):
        usage = {}
    server_tool_use = usage.get("server_tool_use", {})
    if not isinstance(server_tool_use, dict):
        server_tool_use = {}
    web_search_requests = server_tool_use.get("web_search_requests")
    annotations = response_message.get("annotations", [])
    if not isinstance(annotations, list):
        annotations = []
    citation_urls = []
    for annotation in annotations:
        if not isinstance(annotation, dict) or annotation.get("type") != "url_citation":
            continue
        citation = annotation.get("url_citation", {})
        url = citation.get("url") if isinstance(citation, dict) else None
        if isinstance(url, str) and url and url not in citation_urls:
            citation_urls.append(url)
    record_metadata(
        True,
        usage=usage,
        web_search_requests=web_search_requests,
        citation_urls=citation_urls,
    )
    if log_content is None:
        log_content = LOG_AI_CONTENT

    if log_style == "lite":
        log_line = (
            f"AI CALL lite | model={model} | latency={latency_ms:.0f}ms | "
            f"tokens={usage.get('total_tokens', 'N/A')}"
        )
        if web_search_requests is not None:
            log_line += (
                f" | web_searches={web_search_requests}"
                f" | citations={len(citation_urls)}"
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
Web searches: {web_search_requests if web_search_requests is not None else 'N/A'}
Citations: {len(citation_urls)}
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
            purpose="context_filter",
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


async def classify_reply_route(current_message, chat_history=None):
    """Choose normal chat or web-grounded chat for a triggered reply."""
    recent_history = (chat_history or [])[-5:]
    transcript = "\n".join(
        f"{message.get('role', 'user')}: {message.get('content', '')}"
        for message in recent_history
    )
    route_request = (
        f"Recent conversation:\n{transcript or '(none)'}\n\n"
        f"Latest message:\n{current_message}\n\nRoute:"
    )

    try:
        result = await asyncio.to_thread(
            openrouter_chat,
            messages=[
                {"role": "system", "content": REPLY_ROUTE_PROMPT},
                {"role": "user", "content": route_request},
            ],
            model=DEFAULT_FILTER_MODEL,
            reasoning_disabled=True,
            log_style="lite",
            max_tokens=10,
            temperature=0.0,
            purpose="reply_route",
        )
    except Exception as error:
        print(f"Error classifying reply route: {error}")
        return REPLY_ROUTE_CHAT

    if result.strip().lower() == REPLY_ROUTE_SEARCH:
        return REPLY_ROUTE_SEARCH
    return REPLY_ROUTE_CHAT


async def generate_text(
    prompt,
    sysprompt=None,
    gmodel=DEFAULT_TEXT_MODEL,
    chat_history=None,
    use_context_filter=True,
    max_tokens=1200,
):
    """Generate text through OpenRouter, optionally using relevant chat history."""
    clean_prompt = prompt.replace("!gpt5", "").replace("!gpt4", "").replace("!gpt", "").strip()
    if sysprompt is None:
        sysprompt = persona_store.system_prompt()

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
        max_tokens=max_tokens,
        temperature=0.8,
        purpose="generate_text",
    )


def informative_system_prompt(base_prompt):
    """Extend a persona prompt with the more instructional !gpt response mode."""
    return f"{base_prompt.rstrip()}\n\n{INFORMATIVE_MODE_PROMPT.strip()}"


async def generate_text_openrouter(
    cxstorage,
    model=None,
    system_prompt=None,
    enable_web_search=False,
):
    """Generate a response from chat history through OpenRouter."""
    import modules.flipper as flipper

    model = model or flipper.current_model
    if system_prompt is None:
        system_prompt = persona_store.system_prompt()
    if enable_web_search:
        system_prompt = (
            f"{system_prompt.rstrip()}\n\n{WEB_SEARCH_MODE_PROMPT.strip()}"
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
        tools=[WEB_SEARCH_TOOL] if enable_web_search else None,
        purpose=(
            "generate_text_openrouter_search"
            if enable_web_search
            else "generate_text_openrouter"
        ),
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
            purpose="precheck",
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
