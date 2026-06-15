"""Shared configuration."""

import os
from dotenv import load_dotenv

load_dotenv()


# Agent URLs
RESEARCHER_URL = os.getenv("RESEARCHER_URL", "http://localhost:8001")
JUDGE_URL = os.getenv("JUDGE_URL", "http://localhost:8002")
CONTENT_BUILDER_URL = os.getenv("CONTENT_BUILDER_URL", "http://localhost:8003")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8004")

# Iteration limit
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))

# Model config
XIAOMI_API_KEY = os.getenv("XIAOMI_API_KEY")
XIAOMI_API_BASE = os.getenv("XIAOMI_API_BASE", "https://api.xiaomi.ai/v1")
XIAOMI_MODEL = os.getenv("XIAOMI_MODEL", "xiaomi-model-name")

# Tavily
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")