
from openai import OpenAI
import maricon
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
    r = requests.post(
        f"{OPENROUTER_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

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
import os

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

# ============================================================================
# RAG-BASED USER IMPERSONATION (Pete, TK, etc.)
# ============================================================================

# Configuration for different users
USER_CONFIGS = {
    'pete': {
        'file': 'logs/pete.txt',
        'cache': 'logs/pete_chunks_embeddings.pkl',
        'name': 'Pete'
    },
    'tk': {
        'file': 'logs/tk.txt',
        'cache': 'logs/tk_chunks_embeddings.pkl',
        'name': 'TK'
    },
    'breez': {
        'file': 'logs/breez.txt',
        'cache': 'logs/breez_chunks_embeddings.pkl',
        'name': 'Breez'
    }
}

# Global storage for RAG data
user_rag_data = {
    'pete': {'chunks': None, 'embeddings': None, 'config': None},
    'tk': {'chunks': None, 'embeddings': None, 'config': None},
    'breez': {'chunks': None, 'embeddings': None, 'config': None}
}

def load_messages(user_config):
    """Load all messages from the text file"""
    print(f"Loading {user_config['name']}'s messages...")
    with open(user_config['file'], 'r', encoding='utf-8') as f:
        messages = [line.strip() for line in f if line.strip()]
    print(f"Loaded {len(messages)} messages from {user_config['name']}")
    return messages

def create_conversation_chunks(messages, chunk_size=8, overlap=2):
    """
    Create overlapping chunks of consecutive messages (conversation windows)
    This mimics how knowledge bases chunk text for better context retrieval
    """
    print(f"Creating conversation chunks (size={chunk_size}, overlap={overlap})...")
    chunks = []
    
    for i in range(0, len(messages), chunk_size - overlap):
        chunk_messages = messages[i:i + chunk_size]
        if len(chunk_messages) < 3:  # Skip tiny chunks at the end
            break
        
        # Join messages with newlines to form a conversation chunk
        chunk_text = "\n".join(chunk_messages)
        chunks.append({
            'text': chunk_text,
            'messages': chunk_messages,
            'start_idx': i,
            'end_idx': i + len(chunk_messages)
        })
    
    print(f"Created {len(chunks)} conversation chunks")
    return chunks

def create_embeddings(chunks):
    """Create embeddings for conversation chunks"""
    print("Creating embeddings for chunks (this may take a minute)...")
    embeddings = []
    
    # Process in batches
    batch_size = 50
    chunk_texts = [chunk['text'] for chunk in chunks]
    
    for i in range(0, len(chunk_texts), batch_size):
        batch = chunk_texts[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(chunk_texts)-1)//batch_size + 1}...")
        
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=batch
        )
        
        batch_embeddings = [item.embedding for item in response.data]
        embeddings.extend(batch_embeddings)
    
    print("Embeddings created!")
    return np.array(embeddings)

def load_or_create_embeddings(chunks, cache_path):
    """Load cached embeddings or create new ones"""
    if os.path.exists(cache_path):
        print("Loading cached embeddings...")
        with open(cache_path, 'rb') as f:
            cached_data = pickle.load(f)
            if len(cached_data['embeddings']) == len(chunks):
                print("Using cached embeddings!")
                return cached_data['embeddings']
            else:
                print("Cache size mismatch, regenerating...")
    
    # Create new embeddings
    embeddings = create_embeddings(chunks)
    
    # Cache them
    print("Caching embeddings for future use...")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump({'embeddings': embeddings}, f)
    
    return embeddings

def find_similar_chunks(query, chunks, embeddings, top_k=5):
    """Find the most similar conversation chunks using semantic search"""
    # Get embedding for the query
    query_response = client.embeddings.create(
        model="text-embedding-3-large",
        input=[query]
    )
    query_embedding = np.array([query_response.data[0].embedding])
    
    # Calculate cosine similarity
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    
    # Get top k most similar chunks
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    similar_chunks = [
        (chunks[idx], similarities[idx]) 
        for idx in top_indices
    ]
    
    return similar_chunks

def generate_user_message(prompt, similar_chunks, user_name, chat_history=None, rag_model=None):
    """Generate a message using similar conversation chunks and optional chat history.
    rag_model: model to use for generation; defaults to DEFAULT_OPENROUTER_MODEL (OpenRouter).
    """
    if rag_model is None:
        rag_model = DEFAULT_OPENROUTER_MODEL

    # Build context from similar chunks
    context_parts = []
    for i, (chunk, score) in enumerate(similar_chunks[:3], 1):
        context_parts.append(f"Conversation {i}:\n{chunk['text']}")
    
    context = "\n\n".join(context_parts)
    
    # Build recent chat context if provided
    chat_context = ""
    if chat_history and len(chat_history) > 0:
        recent_messages = chat_history[-8:]  # Last 8 messages
        chat_lines = []
        for msg in recent_messages:
            chat_lines.append(f"{msg.get('content', '')}")
        chat_context = f"\n\nRecent conversation:\n" + "\n".join(chat_lines)
    
    system_prompt = f"""You are {user_name} from a Discord chat. Below are some examples of {user_name}'s actual conversations:

{context}
{chat_context}

Based on these examples, respond to the prompt in {user_name}'s voice. Match their:
- Casual, informal tone and grammar
- Sense of humor and topics
- Way of expressing themselves
- Message length and style

Respond naturally as {user_name} would in Discord. Keep it short and conversational."""

    full_prompt = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    if _use_openrouter(rag_model):
        reasoning_disabled = "kimi" in (rag_model or "").lower()
        return _openrouter_chat(full_prompt, rag_model, reasoning_disabled=reasoning_disabled)
    
    response = client.responses.create(
        model=rag_model,
        input=full_prompt
    )
    return response.output_text

def initialize_user_rag_data():
    """Initialize RAG data for all configured users (call on bot startup)"""
    print('Initializing RAG data for user impersonation...')
    global user_rag_data
    
    for user_key in USER_CONFIGS.keys():
        try:
            config = USER_CONFIGS[user_key]
            messages = load_messages(config)
            chunks = create_conversation_chunks(messages, chunk_size=8, overlap=2)
            embeddings = load_or_create_embeddings(chunks, config['cache'])
            user_rag_data[user_key] = {
                'chunks': chunks,
                'embeddings': embeddings,
                'config': config
            }
            print(f'✅ {config["name"]} RAG data loaded successfully')
        except Exception as e:
            print(f'❌ Failed to load {user_key} RAG data: {e}')
    
    print('RAG initialization complete!')
    return user_rag_data

async def handle_user_mention(message_content, mentioned_user, chat_history=None, conversation_context=None):
    """
    Handle user mention and generate response using RAG
    
    Args:
        message_content: The message content
        mentioned_user: The user key ('pete', 'tk', etc.)
        chat_history: Recent chat history (cxstorage format)
        conversation_context: Recent conversation strings (experimental_container format)
    
    Returns:
        Generated response text or None if user data not loaded
    """
    if mentioned_user not in user_rag_data or user_rag_data[mentioned_user]['chunks'] is None:
        print(f'RAG data not loaded for {mentioned_user}')
        return None
    
    try:
        print(f'Generating {mentioned_user} response using RAG...')
        
        # Build comprehensive context for finding similar chunks
        context_parts = []
        
        # Add recent chat history if available
        if chat_history and len(chat_history) > 0:
            recent_chat = chat_history[-6:]  # Last 6 messages
            for msg in recent_chat:
                context_parts.append(msg.get('content', ''))
        
        # Add conversation context if available
        if conversation_context and len(conversation_context) > 0:
            context_parts.extend(conversation_context[-4:])
        
        # Combine or use just the message content
        if context_parts:
            context = "\n".join(context_parts)
        else:
            context = message_content
        
        # Find similar conversation chunks
        similar_chunks = find_similar_chunks(
            context,
            user_rag_data[mentioned_user]['chunks'],
            user_rag_data[mentioned_user]['embeddings'],
            top_k=5
        )
        
        # Generate response with chat history
        response_text = generate_user_message(
            message_content,
            similar_chunks,
            user_rag_data[mentioned_user]['config']['name'],
            chat_history=chat_history
        )
        
        print(f'✅ {mentioned_user} response generated: {response_text}')
        return response_text
        
    except Exception as e:
        print(f'❌ Error generating {mentioned_user} response: {e}')
        import traceback
        traceback.print_exc()
        return None