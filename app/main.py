"""App - Web application that calls Orchestrator."""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
import logging
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format='%(asctime)s [APP] %(message)s')
log = logging.getLogger("app")
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import httpx
from httpx_sse import aconnect_sse

from shared.models import ChatRequest
from shared.config import ORCHESTRATOR_URL

app = FastAPI(title="Course Creation App", description="Web interface for course creation")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP client
httpx_client: httpx.AsyncClient = None


async def get_client() -> httpx.AsyncClient:
    """Get or create HTTP client."""
    global httpx_client
    if httpx_client is None:
        httpx_client = httpx.AsyncClient(timeout=120.0, proxy=None, trust_env=False)
    return httpx_client


@app.post("/api/chat_stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint that calls Orchestrator."""
    client = await get_client()

    async def event_generator():
        try:
            log.info(f"chat_stream called: message={request.message}")
            t0 = time.time()
            # Call orchestrator with streaming
            async with aconnect_sse(
                client,
                "POST",
                f"{ORCHESTRATOR_URL}/run_stream",
                params={"topic": request.message},
            ) as event_source:
                if event_source.response.is_error:
                    # Read error response properly
                    error_body = await event_source.response.aread()
                    yield json.dumps({
                        "type": "error",
                        "error": error_body.decode()
                    }) + "\n"
                else:
                    async for server_event in event_source.aiter_sse():
                        data = server_event.data
                        log.info(f"[SSE] Received event: {data[:120]}")
                        # Parse and forward
                        event = json.loads(data)
                        yield json.dumps(event) + "\n"
                        log.info(f"[SSE] Forwarded event type={event.get('type')}, elapsed={time.time()-t0:.1f}s")
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "error": str(e)
            }) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "app"}


@app.on_event("shutdown")
async def shutdown():
    """Close HTTP client on shutdown."""
    global httpx_client
    if httpx_client:
        await httpx_client.aclose()


# Mount frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)