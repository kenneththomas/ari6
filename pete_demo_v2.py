"""
Pete Message Generator Demo V2
Uses RAG (Retrieval Augmented Generation) with conversation chunking.
Shared data loading and retrieval live in sentience2 (same caches as the bot).
"""

from openai import OpenAI
import maricon
import random

import sentience2
from sentience2 import (
    USER_CONFIGS,
    load_messages,
    create_conversation_chunks,
    load_or_create_embeddings,
    find_similar_chunks,
)

client = OpenAI(api_key=maricon.gptkey)


def generate_message(prompt, similar_chunks, user_name, chat_history=None):
    """Interactive demo: GPT-5.1 generation (not the same model as live sim webhooks)."""
    context_parts = []
    for i, (chunk, score) in enumerate(similar_chunks[:3], 1):
        context_parts.append(f"Conversation {i}:\n{chunk['text']}")

    context = "\n\n".join(context_parts)

    chat_context = ""
    if chat_history and len(chat_history) > 0:
        recent_messages = chat_history[-8:]
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
        {"role": "user", "content": prompt},
    ]

    response = client.responses.create(
        model="gpt-5.1",
        input=full_prompt
    )

    return response.output_text


def show_similar_chunks(similar_chunks, user_name, show_count=6):
    """Display the most similar conversation chunks"""
    print(f"\n📝 Most similar {user_name} conversations:")
    print("=" * 70)
    for i, (chunk, score) in enumerate(similar_chunks[:show_count], 1):
        print(f"\nConversation {i} [similarity: {score:.3f}]:")
        print("-" * 70)
        for msg in chunk['messages'][:6]:
            print(f"  {msg}")
        if len(chunk['messages']) > 6:
            print(f"  ... ({len(chunk['messages'])-6} more messages)")
    print("=" * 70)


def interactive_demo():
    """Run the interactive demo"""
    print("\n" + "="*70)
    print("🤖 MESSAGE GENERATOR V2 - RAG with Conversation Chunks")
    print("="*70)
    print("\nThis uses RAG like the Discord bot (sentience2 shared caches).")
    print("Generation here uses gpt-5.1 for local testing.\n")

    print("Available users:")
    for key, config in USER_CONFIGS.items():
        print(f"  - {key}: {config['name']}")

    while True:
        user_choice = input("\nSelect user (pete/tk/breez): ").strip().lower()
        if user_choice in USER_CONFIGS:
            user_config = USER_CONFIGS[user_choice]
            break
        print("Invalid choice.")

    print(f"\n✅ Selected: {user_config['name']}")

    messages = load_messages(user_config)
    chunk_size = user_config.get('chunk_size', 8)
    overlap = user_config.get('overlap', 2)
    chunks = create_conversation_chunks(messages, chunk_size=chunk_size, overlap=overlap)
    embeddings = load_or_create_embeddings(
        chunks, user_config['cache'], source_file=user_config['file']
    )

    print(f"\n✅ Ready to generate {user_config['name']} messages!")
    print("\nCommands:")
    print(f"  - Type a prompt/context to generate a {user_config['name']} response")
    print("  - Type 'random' to see a random conversation chunk")
    print("  - Type 'switch' to change user")
    print("  - Type 'quit' to exit\n")

    while True:
        print("-" * 70)
        user_input = input("\n🎯 Enter prompt (or 'quit'): ").strip()

        if not user_input:
            continue

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Thanks for testing! Goodbye!")
            break

        if user_input.lower() == 'switch':
            print("\n🔄 Restarting demo to switch user...")
            interactive_demo()
            return

        if user_input.lower() == 'random':
            random_chunk = random.choice(chunks)
            print(f"\n💬 Random {user_config['name']} conversation:")
            print("-" * 70)
            for msg in random_chunk['messages']:
                print(f"  {msg}")
            continue

        print(f"\n🔍 Finding similar {user_config['name']} conversations...")
        similar_chunks = find_similar_chunks(user_input, chunks, embeddings, top_k=6)

        show_similar_chunks(similar_chunks, user_config['name'])

        print(f"\n🤖 Generating {user_config['name']}-style response...")
        generated_response = generate_message(
            user_input, similar_chunks, user_config['name'], chat_history=None
        )

        print("\n" + "="*70)
        print(f"💬 {user_config['name'].upper()} SAYS:")
        print("="*70)
        print(f"{generated_response}")
        print("="*70)


if __name__ == "__main__":
    try:
        interactive_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
