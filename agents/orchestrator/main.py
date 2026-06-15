"""Orchestrator Agent - LangGraph based orchestration."""

import os
import sys
import json
import asyncio
import time
import logging
from typing import Literal, AsyncGenerator
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [ORCHESTRATOR] %(message)s')
log = logging.getLogger("orchestrator")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langgraph.graph import StateGraph, END
import httpx
from httpx_sse import aconnect_sse

from shared.models import (
    CourseState,
    ResearchRequest,
    ResearchResponse,
    JudgeRequest,
    JudgeResponse,
    ContentRequest,
    ContentResponse,
    ProgressEvent,
)
from shared.config import (
    RESEARCHER_URL,
    JUDGE_URL,
    CONTENT_BUILDER_URL,
    MAX_ITERATIONS,
)

log.info(f"Config: RESEARCHER_URL={RESEARCHER_URL}, JUDGE_URL={JUDGE_URL}, CONTENT_BUILDER_URL={CONTENT_BUILDER_URL}")
log.info(f"Config: MAX_ITERATIONS={MAX_ITERATIONS}")

app = FastAPI(title="Orchestrator Agent", description="LangGraph orchestration")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP client for calling other agents
httpx_client: httpx.AsyncClient = None


async def get_client() -> httpx.AsyncClient:
    """Get or create HTTP client."""
    global httpx_client
    if httpx_client is None:
        log.info("Creating new httpx.AsyncClient (timeout=60, trust_env=False)")
        httpx_client = httpx.AsyncClient(timeout=300.0, trust_env=False)
    return httpx_client


# LangGraph Node Functions

async def researcher_node(state: CourseState) -> dict:
    """Call Researcher Agent via HTTP."""
    client = await get_client()
    t0 = time.time()

    request_data = ResearchRequest(
        topic=state["topic"],
        previous_feedback=state.get("judge_feedback") if state["iteration"] > 0 else None
    )

    log.info(f"[researcher] Calling {RESEARCHER_URL}/invoke topic={state['topic']}")
    response = await client.post(
        f"{RESEARCHER_URL}/invoke",
        json=request_data.model_dump(),
    )
    log.info(f"[researcher] Got response in {time.time()-t0:.1f}s, status={response.status_code}")
    response.raise_for_status()
    result = ResearchResponse.model_validate(response.json())
    log.info(f"[researcher] Parsed response, research_output length={len(result.research_output)}")

    return {
        "research_output": result.research_output,
        "research_sources": result.sources,
        "iteration": state["iteration"] + 1,
    }


async def judge_node(state: CourseState) -> dict:
    """Call Judge Agent via HTTP."""
    client = await get_client()
    t0 = time.time()

    request_data = JudgeRequest(
        topic=state["topic"],
        research_output=state["research_output"],
    )

    log.info(f"[judge] Calling {JUDGE_URL}/invoke")
    response = await client.post(
        f"{JUDGE_URL}/invoke",
        json=request_data.model_dump(),
    )
    log.info(f"[judge] Got response in {time.time()-t0:.1f}s, status={response.status_code}")
    response.raise_for_status()
    result = JudgeResponse.model_validate(response.json())
    log.info(f"[judge] status={result.status}, score={result.score}")

    return {
        "judge_status": result.status,
        "judge_feedback": result.feedback,
        "judge_score": result.score,
    }


async def content_builder_node(state: CourseState) -> dict:
    """Call Content Builder Agent via HTTP."""
    client = await get_client()
    t0 = time.time()

    request_data = ContentRequest(
        topic=state["topic"],
        research_output=state["research_output"],
    )

    log.info(f"[content_builder] Calling {CONTENT_BUILDER_URL}/invoke")
    response = await client.post(
        f"{CONTENT_BUILDER_URL}/invoke",
        json=request_data.model_dump(),
    )
    log.info(f"[content_builder] Got response in {time.time()-t0:.1f}s, status={response.status_code}")
    response.raise_for_status()
    result = ContentResponse.model_validate(response.json())
    log.info(f"[content_builder] course_content length={len(result.course_content)}")

    return {
        "final_course": result.course_content,
    }


async def content_builder_node_stream(state: CourseState):
    """Call Content Builder Agent with streaming."""
    client = await get_client()
    t0 = time.time()

    request_data = ContentRequest(
        topic=state["topic"],
        research_output=state["research_output"],
    )

    log.info(f"[content_builder_stream] Calling {CONTENT_BUILDER_URL}/invoke_stream")
    full_content = ""

    async with aconnect_sse(
        client,
        "POST",
        f"{CONTENT_BUILDER_URL}/invoke_stream",
        json=request_data.model_dump(),
    ) as event_source:
        if event_source.response.is_error:
            error_body = await event_source.response.aread()
            log.error(f"[content_builder_stream] Error: {error_body.decode()}")
            raise Exception(f"Content builder error: {error_body.decode()}")

        async for server_event in event_source.aiter_sse():
            data = json.loads(server_event.data)
            if data.get("type") == "chunk":
                chunk = data.get("content", "")
                full_content += chunk
                yield chunk

    log.info(f"[content_builder_stream] Done in {time.time()-t0:.1f}s, total length={len(full_content)}")


def should_continue(state: CourseState) -> Literal["research", "build"]:
    """Determine if we should continue researching or build content."""
    if state["judge_status"] == "pass":
        return "build"
    if state["iteration"] >= state["max_iterations"]:
        return "build"
    return "research"


def build_graph() -> StateGraph:
    """Build the LangGraph state graph."""
    graph = StateGraph(CourseState)
    graph.add_node("researcher", researcher_node)
    graph.add_node("judge", judge_node)
    graph.add_node("content_builder", content_builder_node)
    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "judge")
    graph.add_conditional_edges(
        "judge",
        should_continue,
        {"research": "researcher", "build": "content_builder"}
    )
    graph.add_edge("content_builder", END)
    return graph.compile()


compiled_graph = build_graph()


async def run_graph_with_progress(topic: str) -> AsyncGenerator[ProgressEvent, None]:
    """Run graph and yield progress events."""
    log.info(f"=== Starting run_graph_with_progress for topic='{topic}' ===")
    initial_state: CourseState = {
        "topic": topic,
        "iteration": 0,
        "research_output": None,
        "research_sources": None,
        "judge_status": None,
        "judge_feedback": None,
        "judge_score": None,
        "final_course": None,
        "max_iterations": MAX_ITERATIONS,
    }

    current_state = initial_state

    while True:
        # Researcher step
        log.info("[loop] Yielding researcher progress event")
        yield ProgressEvent(type="progress", agent="researcher", message="正在搜索和整理信息...")
        log.info("[loop] Calling researcher_node...")
        researcher_update = await researcher_node(current_state)
        current_state = {**current_state, **researcher_update}
        log.info("[loop] researcher_node done")

        # Judge step
        log.info("[loop] Yielding judge progress event")
        yield ProgressEvent(type="progress", agent="judge", message="正在评审研究质量...")
        log.info("[loop] Calling judge_node...")
        judge_update = await judge_node(current_state)
        current_state = {**current_state, **judge_update}
        log.info("[loop] judge_node done")

        next_step = should_continue(current_state)
        log.info(f"[loop] should_continue -> {next_step}")

        if next_step == "build":
            log.info("[loop] Yielding content_builder progress event")
            yield ProgressEvent(type="progress", agent="content_builder", message="正在生成课程内容...")
            log.info("[loop] Calling content_builder_node_stream...")
            full_content = ""
            async for chunk in content_builder_node_stream(current_state):
                full_content += chunk
                yield ProgressEvent(type="chunk", content=chunk)
            current_state = {**current_state, "final_course": full_content}
            log.info("[loop] content_builder_node_stream done")

            log.info("[loop] Yielding final result")
            yield ProgressEvent(type="result", course=current_state["final_course"])
            log.info("[loop] === Run complete ===")
            break
        else:
            yield ProgressEvent(
                type="progress",
                agent="judge",
                message=f"评审未通过（第 {current_state['iteration']} 次），继续改进研究..."
            )


@app.post("/run")
async def run(topic: str):
    """Run the orchestration graph."""
    async def event_generator():
        for event in await run_graph_with_progress(topic):
            yield f"data: {json.dumps(event.model_dump())}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/run_stream")
async def run_stream(topic: str):
    """Run with streaming progress events (SSE format)."""
    log.info(f"=== /run_stream called with topic='{topic}' ===")
    async def event_generator():
        async for event in run_graph_with_progress(topic):
            data = f"data: {json.dumps(event.model_dump())}\n\n"
            log.info(f"[SSE] Sending: {data[:100]}")
            yield data
        log.info("[SSE] Stream finished")
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "orchestrator"}


@app.on_event("shutdown")
async def shutdown():
    global httpx_client
    if httpx_client:
        await httpx_client.aclose()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
