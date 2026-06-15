"""Judge Agent - Evaluates research quality and provides feedback."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import time
import logging
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format='%(asctime)s [JUDGE] %(message)s')
log = logging.getLogger("judge")
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import json

from shared.models import JudgeRequest, JudgeResponse
from shared.config import XIAOMI_API_KEY, XIAOMI_API_BASE, XIAOMI_MODEL

app = FastAPI(title="Judge Agent", description="Evaluate research quality")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def evaluate_research(topic: str, research_output: str) -> JudgeResponse:
    """Use LLM to evaluate research quality."""
    client = OpenAI(
        api_key=XIAOMI_API_KEY,
        base_url=XIAOMI_API_BASE,
    )

    prompt = f"""你是一个评审专家，负责评估研究内容的质量。

主题: {topic}

研究内容:
{research_output}

请评估以上研究内容的质量，判断是否适合用于创建课程。

评估标准：
1. 内容完整性：是否覆盖了主题的核心知识点
2. 结构清晰性：内容是否组织有序，便于理解
3. 实用性：是否包含实用的建议或案例
4. 准确性：信息是否准确可靠

请以 JSON 格式输出评估结果：
{{"status": "pass 或 fail", "feedback": "详细的评审反馈，说明优点和需要改进的地方", "score": 0.0 到 1.0 之间的评分}}

如果 status 为 "fail"，feedback 中应明确指出需要补充或改进的具体内容。
如果 status 为 "pass"，feedback 中应总结内容的优点。

只输出 JSON，不要输出其他内容。
"""

    response = client.chat.completions.create(
        model=XIAOMI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    # Parse JSON response
    content = response.choices[0].message.content.strip()

    # Handle potential markdown code blocks
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    try:
        result = json.loads(content)
        return JudgeResponse(
            status=result.get("status", "fail"),
            feedback=result.get("feedback", ""),
            score=result.get("score", 0.5)
        )
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return JudgeResponse(
            status="fail",
            feedback="无法解析评审结果，请重新提交",
            score=0.0
        )


@app.post("/invoke", response_model=JudgeResponse)
async def invoke(request: JudgeRequest) -> JudgeResponse:
    """Main endpoint for Judge Agent."""
    import asyncio

    def _do_judge():
        t0 = time.time()
        log.info(f"invoke called: topic={request.topic}, research_output length={len(request.research_output)}")
        result = evaluate_research(request.topic, request.research_output)
        log.info(f"evaluate_research done in {time.time()-t0:.1f}s, status={result.status}, score={result.score}")
        return result

    return await asyncio.to_thread(_do_judge)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "judge"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)