"""Shared package."""

from .models import (
    CourseState,
    ResearchRequest,
    ResearchResponse,
    JudgeRequest,
    JudgeResponse,
    ContentRequest,
    ContentResponse,
    ChatRequest,
    ProgressEvent,
)
from .llm import get_openai_client, get_langchain_llm
from .config import (
    RESEARCHER_URL,
    JUDGE_URL,
    CONTENT_BUILDER_URL,
    ORCHESTRATOR_URL,
    MAX_ITERATIONS,
    TAVILY_API_KEY,
)

__all__ = [
    "CourseState",
    "ResearchRequest",
    "ResearchResponse",
    "JudgeRequest",
    "JudgeResponse",
    "ContentRequest",
    "ContentResponse",
    "ChatRequest",
    "ProgressEvent",
    "get_openai_client",
    "get_langchain_llm",
    "RESEARCHER_URL",
    "JUDGE_URL",
    "CONTENT_BUILDER_URL",
    "ORCHESTRATOR_URL",
    "MAX_ITERATIONS",
    "TAVILY_API_KEY",
]