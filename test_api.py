#!/usr/bin/env python3
"""Test API connections."""

import os
from dotenv import load_dotenv

load_dotenv()

print("Testing Tavily API...")
try:
    from tavily import TavilyClient
    client = TavilyClient(api_key=os.environ['TAVILY_API_KEY'])
    result = client.search('Python编程', max_results=2)
    print(f"Tavily OK: {len(result.get('results', []))} results")
except Exception as e:
    print(f"Tavily Error: {e}")

print("\nTesting Xiaomi Model API...")
try:
    from openai import OpenAI
    client = OpenAI(
        api_key=os.environ['XIAOMI_API_KEY'],
        base_url=os.environ['XIAOMI_API_BASE'],
    )
    response = client.chat.completions.create(
        model=os.environ['XIAOMI_MODEL'],
        messages=[{'role': 'user', 'content': '你好'}],
        max_tokens=50,
    )
    print(f"Model OK: {response.choices[0].message.content[:50]}")
except Exception as e:
    print(f"Model Error: {e}")