"""Content Builder Agent - Formats research into course content."""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import time
import logging
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s [CONTENT_BUILDER] %(message)s')
log = logging.getLogger("content_builder")
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from shared.models import ContentRequest, ContentResponse
from shared.config import XIAOMI_API_KEY, XIAOMI_API_BASE, XIAOMI_MODEL

app = FastAPI(title="Content Builder Agent", description="Build course content from research")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_course(topic: str, research_output: str) -> str:
    """Use LLM to format research into a course."""
    client = OpenAI(
        api_key=XIAOMI_API_KEY,
        base_url=XIAOMI_API_BASE,
    )

    prompt = f"""你是一个课程内容创作者，需要将研究内容整理成结构化的课程模块。

主题: {topic}

研究内容:
{research_output}

请根据以上研究内容，创建一个完整的课程模块。

要求：
1. 严格使用 Markdown 格式，使用 # ## ### 等 Markdown 语法标记标题层级，不要使用 HTML 标签
2. 包含课程标题、学习目标、主要内容章节、总结和练习建议
3. 内容要结构清晰，便于学习者理解
4. 添加适当的示例和说明

输出格式示例：

# {topic} 课程

## 学习目标
- 目标1
- 目标2

## 第一章：基础概念
...

## 第二章：核心原理
...

## 总结
...

## 练习建议
...

请输出完整的课程内容（纯 Markdown 格式，不要使用 HTML 标签）：
"""

    response = client.chat.completions.create(
        model=XIAOMI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    return response.choices[0].message.content


def build_course_stream(topic: str, research_output: str):
    """Use LLM to format research into a course with streaming."""
    client = OpenAI(
        api_key=XIAOMI_API_KEY,
        base_url=XIAOMI_API_BASE,
    )

    prompt = f"""你是一个课程内容创作者，需要将研究内容整理成结构化的课程模块。

主题: {topic}

研究内容:
{research_output}

请根据以上研究内容，创建一个完整的课程模块。

要求：
1. 严格使用 Markdown 格式，使用 # ## ### 等 Markdown 语法标记标题层级，不要使用 HTML 标签
2. 包含课程标题、学习目标、主要内容章节、总结和练习建议
3. 内容要结构清晰，便于学习者理解
4. 添加适当的示例和说明

输出格式示例：

# {topic} 课程

## 学习目标
- 目标1
- 目标2

## 第一章：基础概念
...

## 第二章：核心原理
...

## 总结
...

## 练习建议
...

请输出完整的课程内容（纯 Markdown 格式，不要使用 HTML 标签）：
"""

    stream = client.chat.completions.create(
        model=XIAOMI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


@app.post("/invoke", response_model=ContentResponse)
async def invoke(request: ContentRequest) -> ContentResponse:
    """Main endpoint for Content Builder Agent."""
    import asyncio

    def _do_build():
        t0 = time.time()
        log.info(f"invoke called: topic={request.topic}, research_output length={len(request.research_output)}")
        result = build_course(request.topic, request.research_output)
        log.info(f"build_course done in {time.time()-t0:.1f}s, output length={len(result)}")
        return result

    course_content = await asyncio.to_thread(_do_build)

    return ContentResponse(
        course_content=course_content,
        format="markdown"
    )


@app.post("/invoke_stream")
async def invoke_stream(request: ContentRequest):
    """Streaming endpoint for Content Builder Agent."""
    import asyncio

    t0 = time.time()
    log.info(f"invoke_stream called: topic={request.topic}, research_output length={len(request.research_output)}")

    def event_generator():
        for content in build_course_stream(request.topic, request.research_output):
            yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
        log.info(f"invoke_stream done in {time.time()-t0:.1f}s")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "content_builder"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)