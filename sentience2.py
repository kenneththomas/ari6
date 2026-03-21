
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

SIM_MENTION_RE = re.compile(r'@(pete|tk|breez)\b', re.IGNORECASE)
# Retrieve more candidates than we inject, then dedupe by chunk start for diversity
SIM_RETRIEVAL_POOL = 12
SIM_RAG_TOP_K = 3
DISCORD_MESSAGE_MAX = 2000


def strip_sim_mentions(text):
    """Remove @pete/@tk/@breez so retrieval and generation match message substance."""
    if not text:
        return ''
    return SIM_MENTION_RE.sub('', text).strip()


def dedupe_chunks_by_start_idx(similar_chunks, max_k=SIM_RAG_TOP_K):
    """Prefer diverse windows: skip chunks that share the same conversation start index."""
    seen = set()
    out = []
    for chunk, score in similar_chunks:
        sid = chunk['start_idx']
        if sid in seen:
            continue
        seen.add(sid)
        out.append((chunk, score))
        if len(out) >= max_k:
            break
    return out


# Configuration for different users (optional: chunk_size, overlap, rag_model)
USER_CONFIGS = {
    'pete': {
        'file': 'logs/pete.txt',
        'cache': 'logs/pete_chunks_embeddings.pkl',
        'name': 'Pete',
        'rag_model': DEFAULT_OPENROUTER_MODEL,
    },
    'tk': {
        'file': 'logs/tk.txt',
        'cache': 'logs/tk_chunks_embeddings.pkl',
        'name': 'TK',
        'rag_model': DEFAULT_OPENROUTER_MODEL,
    },
    'breez': {
        'file': 'logs/breez.txt',
        'cache': 'logs/breez_chunks_embeddings.pkl',
        'name': 'Breez',
        'rag_model': DEFAULT_OPENROUTER_MODEL,
    },
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

def load_or_create_embeddings(chunks, cache_path, source_file=None):
    """Load cached embeddings or create new ones. Invalidates cache when log file is newer than cache."""
    src_mtime = os.path.getmtime(source_file) if source_file and os.path.isfile(source_file) else None

    if os.path.exists(cache_path):
        print("Loading cached embeddings...")
        with open(cache_path, 'rb') as f:
            cached_data = pickle.load(f)
        if not isinstance(cached_data, dict):
            cached_data = {'embeddings': cached_data}
        embeddings = cached_data['embeddings']
        cached_mtime = cached_data.get('source_mtime')

        if len(embeddings) == len(chunks):
            stale = False
            if src_mtime is not None and cached_mtime is not None and cached_mtime < src_mtime:
                stale = True
            if not stale:
                print("Using cached embeddings!")
                return np.array(embeddings)
        print("Cache size mismatch or source log newer than cache, regenerating...")

    embeddings = create_embeddings(chunks)

    print("Caching embeddings for future use...")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    payload = {'embeddings': embeddings}
    if src_mtime is not None:
        payload['source_mtime'] = src_mtime
    with open(cache_path, 'wb') as f:
        pickle.dump(payload, f)

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

def generate_user_message(
    prompt,
    similar_chunks,
    user_name,
    chat_history=None,
    rag_model=None,
    persona_bio=None,
):
    """Generate a message using similar conversation chunks and optional chat history.
    rag_model: model to use for generation; defaults to DEFAULT_OPENROUTER_MODEL (OpenRouter).
    persona_bio: optional one-liner from webhook metadata for stable identity hints.
    """
    if rag_model is None:
        rag_model = DEFAULT_OPENROUTER_MODEL

    context_parts = []
    for i, (chunk, score) in enumerate(similar_chunks[:SIM_RAG_TOP_K], 1):
        context_parts.append(f"Conversation {i}:\n{chunk['text']}")

    context = "\n\n".join(context_parts)

    chat_context = ""
    if chat_history and len(chat_history) > 0:
        recent_messages = chat_history[-8:]
        chat_lines = [f"{msg.get('content', '')}" for msg in recent_messages]
        chat_context = f"\n\nRecent conversation:\n" + "\n".join(chat_lines)

    bio_line = f"\nNote about this person: {persona_bio}\n" if persona_bio else ""

    system_prompt = f"""You are {user_name} from a Discord chat. Below are some examples of {user_name}'s actual conversations:

{context}
{chat_context}
{bio_line}
Based on these examples, respond to the prompt in {user_name}'s voice. Match their:
- Casual, informal tone and grammar
- Sense of humor and topics
- Way of expressing themselves
- Message length and style

Do not mention training data, examples, RAG, or "based on the above". Stay in character as {user_name} only.

Respond naturally as {user_name} would in Discord. Keep it short and conversational."""

    full_prompt = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    if _use_openrouter(rag_model):
        reasoning_disabled = "kimi" in (rag_model or "").lower()
        text = _openrouter_chat(full_prompt, rag_model, reasoning_disabled=reasoning_disabled)
    else:
        response = client.responses.create(
            model=rag_model,
            input=full_prompt
        )
        text = response.output_text

    if text and len(text) > DISCORD_MESSAGE_MAX:
        text = text[: DISCORD_MESSAGE_MAX - 1] + "…"
    return text

def _load_one_user_rag(user_key):
    """Load chunks + embeddings for one sim user into user_rag_data."""
    global user_rag_data
    config = USER_CONFIGS[user_key]
    messages = load_messages(config)
    chunk_size = config.get('chunk_size', 8)
    overlap = config.get('overlap', 2)
    chunks = create_conversation_chunks(messages, chunk_size=chunk_size, overlap=overlap)
    embeddings = load_or_create_embeddings(chunks, config['cache'], source_file=config['file'])
    user_rag_data[user_key] = {
        'chunks': chunks,
        'embeddings': embeddings,
        'config': config,
    }
    print(f'✅ {config["name"]} RAG data loaded successfully')


def initialize_user_rag_data():
    """Initialize RAG data for all configured users (call on bot startup)"""
    print('Initializing RAG data for user impersonation...')
    global user_rag_data

    for user_key in USER_CONFIGS.keys():
        try:
            _load_one_user_rag(user_key)
        except Exception as e:
            print(f'❌ Failed to load {user_key} RAG data: {e}')

    print('RAG initialization complete!')
    return user_rag_data


def reload_user_rag_data(user_key=None):
    """
    Reload sim RAG from disk (e.g. after log export). Pass one of pete/tk/breez, or None for all.
    """
    global user_rag_data
    keys = [user_key] if user_key else list(USER_CONFIGS.keys())
    for key in keys:
        if key not in USER_CONFIGS:
            print(f'Unknown sim user key: {key}')
            continue
        try:
            _load_one_user_rag(key)
        except Exception as e:
            print(f'❌ Failed to reload {key}: {e}')


def _sim_generation_sync(
    stripped_prompt,
    retrieval_query,
    mentioned_user,
    chat_history,
    rag_model,
    persona_bio,
):
    """Sync work for embedding retrieval + chat completion (run in a thread)."""
    ud = user_rag_data[mentioned_user]
    similar_chunks = find_similar_chunks(
        retrieval_query,
        ud['chunks'],
        ud['embeddings'],
        top_k=SIM_RETRIEVAL_POOL,
    )
    similar_chunks = dedupe_chunks_by_start_idx(similar_chunks, SIM_RAG_TOP_K)
    return generate_user_message(
        stripped_prompt,
        similar_chunks,
        ud['config']['name'],
        chat_history=chat_history,
        rag_model=rag_model,
        persona_bio=persona_bio,
    )


async def handle_user_mention(
    message_content,
    mentioned_user,
    chat_history=None,
    conversation_context=None,
    persona_bio=None,
    rag_model=None,
):
    """
    Handle user mention and generate response using RAG
    
    Args:
        message_content: The message content
        mentioned_user: The user key ('pete', 'tk', etc.)
        chat_history: Recent chat history (cxstorage format)
        conversation_context: Recent conversation strings (experimental_container format)
        persona_bio: Optional one-liner for the system prompt (e.g. from webhook library)
        rag_model: Optional override; defaults to USER_CONFIGS[mentioned_user]['rag_model']
    
    Returns:
        Generated response text or None if user data not loaded
    """
    if mentioned_user not in user_rag_data or user_rag_data[mentioned_user]['chunks'] is None:
        print(f'RAG data not loaded for {mentioned_user}')
        return None

    try:
        print(f'Generating {mentioned_user} response using RAG...')
        cfg = user_rag_data[mentioned_user]['config']
        if rag_model is None:
            rag_model = cfg.get('rag_model', DEFAULT_OPENROUTER_MODEL)

        stripped = strip_sim_mentions(message_content)

        context_parts = []
        if chat_history:
            relevant = await filter_relevant_messages(stripped, chat_history)
            if relevant:
                for msg in relevant:
                    context_parts.append(msg.get('content', ''))
            else:
                for msg in chat_history[-6:]:
                    context_parts.append(msg.get('content', ''))
        if conversation_context:
            context_parts.extend(conversation_context[-4:])

        retrieval_query = "\n".join(context_parts) if context_parts else stripped

        response_text = await asyncio.to_thread(
            _sim_generation_sync,
            stripped,
            retrieval_query,
            mentioned_user,
            chat_history,
            rag_model,
            persona_bio,
        )

        print(f'✅ {mentioned_user} response generated: {response_text}')
        return response_text

    except Exception as e:
        print(f'❌ Error generating {mentioned_user} response: {e}')
        import traceback
        traceback.print_exc()
        return None