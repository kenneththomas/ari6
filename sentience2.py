
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

async def generate_text_gpt(prompt, gmodel='gpt-5-mini'):
    full_prompt = [
        {"role": "system", "content": f"you are Ari, you are posting in a discord channel. you will respond with short informal messages. you will not refer to yourself as an AI"},
        {"role": "user", "content": f"{prompt}"}
    ]
    response = client.responses.create(
    model=gmodel,
    input=full_prompt)
    return response.output_text