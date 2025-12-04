
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
    
    response = client.responses.create(
        model=gmodel,
        input=full_prompt)
    return response.output_text