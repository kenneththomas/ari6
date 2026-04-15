
from openai import OpenAI
import maricon
import os

client = OpenAI(api_key=maricon.gptkey)

# OpenRouter: same as Chat Completions API; use when model id contains "/" (e.g. moonshotai/kimi-k2.5)
DEFAULT_OPENROUTER_MODEL = "moonshotai/kimi-k2.5"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

def _use_openrouter(model):
    """True if model should be sent to OpenRouter (provider/model id)."""
    return "/" in (model or "")

def _openrouter_chat(messages, model, reasoning_disabled=False):
    """Call OpenRouter chat completions; returns response text or raises."""
    key = (getattr(maricon, "openrouter_key", None) or os.environ.get("OPENROUTER_API_KEY") or "")
    if not key:
        raise ValueError("OpenRouter requested but openrouter_key (or OPENROUTER_API_KEY) not set")
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.0,
    }
    if reasoning_disabled:
        payload["reasoning"] = {"enabled": False}

    start_time = time.time()

    r = requests.post(
        f"{OPENROUTER_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()

    latency_ms = (time.time() - start_time) * 1000

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})

    input_summary = [{"role": m["role"], "content": m["content"][:100] + "..." if len(m.get("content", "")) > 100 else m.get("content", "")} for m in messages]

    print(f"""
=== AI CALL ===
Model: {model}
Input tokens: {usage.get('prompt_tokens', 'N/A')}
Output tokens: {usage.get('completion_tokens', 'N/A')}
Total tokens: {usage.get('total_tokens', 'N/A')}
Latency: {latency_ms:.0f}ms
Input: {input_summary}
Output: {content}
==============
""")

    return content

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
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle

async def filter_relevant_messages(current_message, chat_history, filter_model='gpt-5-mini'):
    """
    Use GPT-5-mini to filter chat history and return only messages relevant to the current query.
    
    Args:
        current_message: The user's current message/query
        chat_history: List of message dicts with 'role' and 'content' keys
        filter_model: Model to use for filtering
        
    Returns:
        List of relevant message dicts from chat_history
    """
    if not chat_history or len(chat_history) == 0:
        return []
    
    # Number the messages for easier reference (only consider last 10 for efficiency)
    recent_messages = chat_history[-10:]
    numbered_history = []
    for i, msg in enumerate(recent_messages, start=1):
        numbered_history.append(f"{i}. {msg.get('role', 'user')}: {msg.get('content', '')}")
    
    history_text = "\n".join(numbered_history)
    
    filter_prompt = f"""You are analyzing chat history to find messages relevant to a user's query.

Current user query: "{current_message}"

Chat history (most recent messages, numbered):
{history_text}

Task: Identify which messages are relevant to answering the current query.
- Include messages that provide context, continue the topic, or are part of the same conversation thread
- Exclude messages that are completely unrelated (different topics, random chatter)

Return ONLY a comma-separated list of numbers (1-{len(numbered_history)}) corresponding to relevant messages.
If no messages are relevant, return "none".

Example: "1,3,5" or "none"
"""
    
    try:
        filter_response = client.chat.completions.create(
            model=filter_model,
            messages=[{"role": "user", "content": filter_prompt}],
            max_tokens=50,
            temperature=0.0
        )
        
        result = filter_response.choices[0].message.content.strip().lower()
        
        # Extract just the numbers from the response (handle cases where GPT adds explanation)
        numbers = re.findall(r'\d+', result)
        
        if not numbers or result == "none":
            print(f"No relevant messages found for query: {current_message[:50]}...")
            return []
        
        # Parse indices (convert from 1-based to 0-based)
        try:
            relevant_indices = [int(num) - 1 for num in numbers]
            # Filter to valid indices and get corresponding messages
            recent_messages = chat_history[-10:]
            relevant_messages = [
                recent_messages[idx] 
                for idx in relevant_indices 
                if 0 <= idx < len(recent_messages)
            ]
            print(f"Filtered {len(relevant_messages)} relevant messages from {len(recent_messages)} recent messages")
            return relevant_messages
        except (ValueError, IndexError) as e:
            print(f"Error parsing filter response '{result}': {e}")
            return []
            
    except Exception as e:
        print(f"Error filtering messages: {e}")
        # On error, return empty list to proceed without context
        return []

async def generate_text_gpt(prompt, gmodel='gpt-5-mini', chat_history=None, use_context_filter=True):
    """
    Generate text using GPT with optional chat history context.
    
    Args:
        prompt: The user's message/query
        gmodel: The GPT model to use for generation
        chat_history: Optional list of message dicts with 'role' and 'content' keys
        use_context_filter: If True and chat_history is provided, filter for relevant messages first
    """
    # Remove command prefix from prompt
    clean_prompt = prompt.replace('!gpt5', '').replace('!gpt', '').strip()
    
    # Build context messages
    context_messages = []
    
    if chat_history and use_context_filter:
        # Filter chat history for relevant messages
        relevant_messages = await filter_relevant_messages(clean_prompt, chat_history)
        context_messages = relevant_messages
    
    # Build the full prompt with context
    full_prompt = [
        {"role": "system", "content": f"you are Ari, you are posting in a discord channel. you will respond with short informal messages. you will not refer to yourself as an AI"},
    ]
    
    # Add context messages if any
    for msg in context_messages:
        full_prompt.append({
            "role": msg.get('role', 'user'),
            "content": msg.get('content', '')
        })
    
    # Add the current user query
    full_prompt.append({"role": "user", "content": clean_prompt})

    if _use_openrouter(gmodel):
        reasoning_disabled = "kimi" in (gmodel or "").lower()
        return _openrouter_chat(full_prompt, gmodel, reasoning_disabled=reasoning_disabled)

    response = client.responses.create(
        model=gmodel,
        input=full_prompt)
    return response.output_text


async def generate_text_openrouter(cxstorage, model=None, system_prompt=None):
    """
    Generate text using OpenRouter for any model (Anthropic, OpenAI, etc.).

    Args:
        cxstorage: List of message dicts with 'role' and 'content' keys
        model: Model identifier (e.g., 'anthropic/claude-sonnet-4-6'). Defaults to flipper.current_model.
        system_prompt: Optional system prompt. If None, uses default Ari persona.

    Returns:
        Generated response text
    """
    import modules.flipper as flipper

    if model is None:
        model = flipper.current_model

    if system_prompt is None:
        system_prompt = f"the current time is {datetime.datetime.now(pytz.timezone('America/New_York')).strftime('%A, %Y-%m-%d %H:%M:%S')}. you are roleplaying as ari, posting in an groupchat. you are a 27 year old girl from NYC. your family is jewish. you speak in a very casual and informal style, limit use of punctuation. keep messages brief unless there's something funny to say (encouraged) and you can go up to like 3 sentences. longer form is ok if answering a specific question. no emojis. the chat is referred to as \'gato\' and the people in the chat are jokingly referred to as gato members. gato is referred to as \'this gato\'. You will not refer to yourself as an AI or use a lecturing tone, emojis, or hashtags. Avoid starting messages with a greeting. if you are upset with someone, your favorite insult to use is calling someone a dog. You love offensive/crude humor. nothing surprises you."

    full_prompt = [{"role": "system", "content": system_prompt}]

    for msg in cxstorage:
        full_prompt.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })

    reasoning_disabled = "kimi" in (model or "").lower()
    return _openrouter_chat(full_prompt, model, reasoning_disabled=reasoning_disabled)