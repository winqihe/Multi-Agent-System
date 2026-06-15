"""Researcher Agent - Uses Tavily API to search for information."""

import os
import sys
from typing import List
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import time
import logging
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format='%(asctime)s [RESEARCHER] %(message)s')
log = logging.getLogger("researcher")
from fastapi.middleware.cors import CORSMiddleware
from tavily import TavilyClient
from openai import OpenAI

from shared.models import ResearchRequest, ResearchResponse
from shared.config import TAVILY_API_KEY, XIAOMI_API_KEY, XIAOMI_API_BASE, XIAOMI_MODEL

app = FastAPI(title="Researcher Agent", description="Search and gather information")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def search_with_tavily(query: str, max_results: int = 5) -> dict:
    """Search using Tavily API. Returns empty results on failure."""
    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(query, max_results=max_results, search_depth="advanced")
        return response
    except Exception as e:
        log.warning(f"Tavily search failed: {e}, falling back to LLM-only research")
        return {"results": []}


def summarize_results(search_results: dict, topic: str, previous_feedback: str = None) -> str:
    """Use LLM to summarize and synthesize search results."""
    client = OpenAI(
        api_key=XIAOMI_API_KEY,
        base_url=XIAOMI_API_BASE,
    )

    # Build context from search results
    context_parts = []
    for result in search_results.get("results", []):
        context_parts.append(f"Source: {result.get('url', 'N/A')}\nContent: {result.get('content', '')}")

    context = "\n\n".join(context_parts)

    # Build prompt
    if context:
        prompt = f"""你是一个研究助手，需要为课程创作收集和整理信息。

主题: {topic}

以下是搜索到的相关信息:
{context}

请根据以上信息，整理出关于该主题的核心知识点、重要概念和实用建议。
输出应该结构清晰，便于后续评审和课程编写。
"""
    else:
        prompt = f"""你是一个研究助手，需要为课程创作收集和整理信息。

主题: {topic}

请根据你的知识，详细整理出关于该主题的核心知识点、重要概念和实用建议。
输出应该结构清晰，便于后续评审和课程编写。请确保内容全面、准确、有深度。
"""

    if previous_feedback:
        prompt += f"""
注意：上一轮评审反馈如下，请在研究中改进:
{previous_feedback}

"""

    prompt += "请输出整理后的研究内容（不需要列出来源链接，只需整理内容）："

    response = client.chat.completions.create(
        model=XIAOMI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return response.choices[0].message.content


def extract_sources(search_results: dict) -> List[str]:
    """Extract source URLs from search results."""
    return [r.get("url", "") for r in search_results.get("results", []) if r.get("url")]


@app.post("/invoke", response_model=ResearchResponse)
async def invoke(request: ResearchRequest) -> ResearchResponse:
    """Main endpoint for Researcher Agent."""
    import asyncio

    def _do_research():
        t0 = time.time()
        log.info(f"invoke called: topic={request.topic}")

        query = request.topic
        if request.previous_feedback:
            query = f"{request.topic} - focusing on areas mentioned in feedback"

        log.info(f"Searching Tavily: query='{query}'")
        search_results = search_with_tavily(query, max_results=5)
        log.info(f"Tavily done in {time.time()-t0:.1f}s, got {len(search_results.get('results', []))} results")

        log.info("Calling LLM to summarize...")
        t1 = time.time()
        research_output = summarize_results(
            search_results,
            request.topic,
            request.previous_feedback
        )
        log.info(f"LLM summarize done in {time.time()-t1:.1f}s, output length={len(research_output)}")

        sources = extract_sources(search_results)
        log.info(f"Total invoke time: {time.time()-t0:.1f}s")

        return ResearchResponse(
            research_output=research_output,
            sources=sources
        )

    return await asyncio.to_thread(_do_research)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "researcher"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)