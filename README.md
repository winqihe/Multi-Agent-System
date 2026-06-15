# Course Creation Multi-Agent System

基于 LangGraph 的多 Agent 课程创作系统，通过 Researcher、Judge、Content Builder 三个 Agent 协作，自动生成高质量课程内容。

## Features

- **多 Agent 协作**: Researcher 搜索信息 → Judge 评审质量 → Content Builder 生成课程
- **流式输出**: Content Builder 支持 SSE 流式输出，前端实时展示生成过程
- **质量保证**: Judge Agent 评估研究质量，不合格则返回 Researcher 改进（最多 3 轮）
- **Web 界面**: 提供简洁的 Web UI，输入主题即可生成课程
- **容错机制**: Tavily 搜索失败时自动回退到 LLM 知识生成

## Architecture

```
用户浏览器 (http://localhost:8000)
        │
        ▼
┌─────────────────────────────────────┐
│         App (Web 应用)              │
│       FastAPI + SSE 流式响应        │
└─────────────────┬───────────────────┘
                  │ HTTP
                  ▼
┌─────────────────────────────────────┐
│       Orchestrator (编排器)          │
│     LangGraph StateGraph            │
│                                     │
│  Researcher → Judge → (循环)        │
│                 ↓ pass              │
│           Content Builder           │
└─────────────────┬───────────────────┘
                  │ HTTP
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌─────────┐ ┌─────────┐ ┌─────────────┐
│Researcher│ │  Judge  │ │Content      │
│  8001    │ │  8002   │ │Builder 8003 │
│Tavily搜索│ │评审质量  │ │格式化课程    │
└─────────┘ └─────────┘ └─────────────┘
```

## Quick Start

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Keys:

```env
# 小米模型 API（OpenAI 协议兼容）
XIAOMI_API_BASE=https://api.xiaomi.ai/v1
XIAOMI_API_KEY=your-xiaomi-api-key
XIAOMI_MODEL=your-model-name

# Tavily 搜索 API
TAVILY_API_KEY=your-tavily-key
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 启动服务

```bash
./run_local.sh
```

### 4. 访问应用

打开浏览器访问 http://localhost:8000

## Project Structure

```
multi-agent-system/
├── agents/
│   ├── researcher/          # 研究者 Agent (Tavily 搜索 + LLM 整理)
│   │   └── main.py
│   ├── judge/               # 评审 Agent (评估研究质量)
│   │   └── main.py
│   ├── content_builder/     # 内容构建 Agent (生成课程)
│   │   └── main.py
│   └── orchestrator/        # LangGraph 编排器
│       └── main.py
├── app/                     # Web 应用
│   ├── main.py
│   └── frontend/
│       ├── index.html
│       ├── app.js
│       └── style.css
├── shared/                  # 共享模块
│   ├── models.py            # Pydantic 数据模型
│   ├── llm.py               # LLM 客户端配置
│   └── config.py            # 环境变量配置
├── pyproject.toml           # 项目依赖
├── run_local.sh             # 启动脚本
├── stop.sh                  # 停止脚本
└── .env.example             # 环境变量模板
```

## API Reference

### Researcher Agent (8001)

```http
POST /invoke
Content-Type: application/json

{
    "topic": "机器学习基础",
    "previous_feedback": "需要更多内容（可选）"
}

Response:
{
    "research_output": "研究内容...",
    "sources": ["url1", "url2"]
}
```

### Judge Agent (8002)

```http
POST /invoke
Content-Type: application/json

{
    "topic": "机器学习基础",
    "research_output": "研究内容..."
}

Response:
{
    "status": "pass",
    "feedback": "评审反馈",
    "score": 0.85
}
```

### Content Builder Agent (8003)

```http
POST /invoke
Content-Type: application/json

{
    "topic": "机器学习基础",
    "research_output": "研究内容..."
}

Response:
{
    "course_content": "# 课程内容...",
    "format": "markdown"
}
```

### Content Builder Streaming (8003)

```http
POST /invoke_stream
Content-Type: application/json

{
    "topic": "机器学习基础",
    "research_output": "研究内容..."
}

Response (SSE):
data: {"type": "chunk", "content": "# 课程"}
data: {"type": "chunk", "content": "\n\n## 学习目标"}
...
```

### Orchestrator (8004)

```http
POST /run_stream?topic=机器学习基础

Response (SSE):
data: {"type": "progress", "agent": "researcher", "message": "正在搜索..."}
data: {"type": "progress", "agent": "judge", "message": "正在评审..."}
data: {"type": "progress", "agent": "content_builder", "message": "正在生成..."}
data: {"type": "chunk", "content": "# 课程内容片段..."}
data: {"type": "result", "course": "完整课程内容..."}
```

## Workflow

1. 用户输入课程主题
2. **Researcher**: 使用 Tavily 搜索相关信息，LLM 整理内容
3. **Judge**: 评估研究质量，输出 pass/fail + 反馈
4. 如果 fail，返回 Researcher 改进（最多循环 3 次）
5. 如果 pass，进入 **Content Builder**
6. **Content Builder**: 将研究内容格式化为 Markdown 课程（流式输出）

## Tech Stack

- **编排**: LangGraph (状态机)
- **LLM**: OpenAI SDK (兼容小米模型)
- **搜索**: Tavily API
- **Web**: FastAPI + SSE
- **前端**: 原生 JS + marked.js
- **依赖管理**: uv

## Configuration

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `XIAOMI_API_BASE` | 小米模型 API 地址 | `https://api.xiaomi.ai/v1` |
| `XIAOMI_API_KEY` | 小米模型 API Key | - |
| `XIAOMI_MODEL` | 模型名称 | - |
| `TAVILY_API_KEY` | Tavily 搜索 API Key | - |
| `MAX_ITERATIONS` | 最大循环次数 | `3` |

## Development

### 停止服务

```bash
./stop.sh
```

### 运行测试

```bash
# 测试单个 Agent API
python test_api.py

# 测试完整流程
python test_flow.py
```

### 手动启动单个服务

```bash
# 启动 Researcher
uv run uvicorn agents.researcher.main:app --port 8001

# 启动 Judge
uv run uvicorn agents.judge.main:app --port 8002

# 启动 Content Builder
uv run uvicorn agents.content_builder.main:app --port 8003

# 启动 Orchestrator
uv run uvicorn agents.orchestrator.main:app --port 8004

# 启动 Web App
uv run uvicorn app.main:app --port 8000
```

## License

MIT
