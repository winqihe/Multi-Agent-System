#!/bin/bash

# Course Creation Multi-Agent System - Local Startup Script

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found. Using .env.example as template."
    echo "Please copy .env.example to .env and configure your API keys."
    exit 1
fi

# Kill existing processes on ports
echo "Stopping any existing processes on ports 8000-8004..."
lsof -ti:8000,8001,8002,8003,8004 | xargs kill -9 2>/dev/null || true

# Install dependencies if needed
echo "Checking dependencies..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment and installing dependencies..."
    uv venv
    uv sync
fi

# Start Researcher Agent
echo "Starting Researcher Agent on port 8001..."
uv run uvicorn agents.researcher.main:app --host 0.0.0.0 --port 8001 &
RESEARCHER_PID=$!
sleep 1

# Start Judge Agent
echo "Starting Judge Agent on port 8002..."
uv run uvicorn agents.judge.main:app --host 0.0.0.0 --port 8002 &
JUDGE_PID=$!
sleep 1

# Start Content Builder Agent
echo "Starting Content Builder Agent on port 8003..."
uv run uvicorn agents.content_builder.main:app --host 0.0.0.0 --port 8003 &
CONTENT_BUILDER_PID=$!
sleep 1

# Start Orchestrator
echo "Starting Orchestrator Agent on port 8004..."
uv run uvicorn agents.orchestrator.main:app --host 0.0.0.0 --port 8004 &
ORCHESTRATOR_PID=$!
sleep 2

# Start Web App
echo "Starting Web App on port 8000..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
APP_PID=$!

echo ""
echo "=========================================="
echo "All services started successfully!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Researcher:      http://localhost:8001"
echo "  - Judge:           http://localhost:8002"
echo "  - Content Builder: http://localhost:8003"
echo "  - Orchestrator:    http://localhost:8004"
echo "  - Web App:         http://localhost:8000"
echo ""
echo "Open http://localhost:8000 in your browser to use the app."
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

# Wait for all processes
trap "echo 'Stopping services...'; kill $RESEARCHER_PID $JUDGE_PID $CONTENT_BUILDER_PID $ORCHESTRATOR_PID $APP_PID 2>/dev/null; exit 0" INT TERM
wait