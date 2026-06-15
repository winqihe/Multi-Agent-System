#!/bin/bash

# Stop all running services

echo "Stopping services on ports 8000-8004..."
lsof -ti:8000,8001,8002,8003,8004 | xargs kill -9 2>/dev/null || true
echo "All services stopped."