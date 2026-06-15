"""LLM client configuration for Xiaomi model (OpenAI protocol compatible)."""

import os
from openai import OpenAI
from langchain_openai import ChatOpenAI


def get_openai_client() -> OpenAI:
    """Get OpenAI client configured for Xiaomi model."""
    return OpenAI(
        api_key=os.getenv("XIAOMI_API_KEY"),
        base_url=os.getenv("XIAOMI_API_BASE", "https://api.xiaomi.ai/v1"),
    )


def get_langchain_llm(temperature: float = 0.7) -> ChatOpenAI:
    """Get LangChain ChatOpenAI configured for Xiaomi model."""
    return ChatOpenAI(
        api_key=os.getenv("XIAOMI_API_KEY"),
        base_url=os.getenv("XIAOMI_API_BASE", "https://api.xiaomi.ai/v1"),
        model=os.getenv("XIAOMI_MODEL", "xiaomi-model-name"),
        temperature=temperature,
    )