#!/usr/bin/env python3
"""Start all services with proper environment loading."""

import os
import subprocess
import time
import signal

# Load environment from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
with open(env_path) as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            key, val = line.strip().split('=', 1)
            os.environ[key] = val

print("Environment loaded:")
print(f"  XIAOMI_API_BASE: {os.environ.get('XIAOMI_API_BASE')}")
print(f"  XIAOMI_MODEL: {os.environ.get('XIAOMI_MODEL')}")
print(f"  TAVILY_API_KEY: {os.environ.get('TAVILY_API_KEY', '')[:20]}...")

# Start all services
services = [
    ('agents.researcher.main:app', 8001),
    ('agents.judge.main:app', 8002),
    ('agents.content_builder.main:app', 8003),
    ('agents.orchestrator.main:app', 8004),
    ('app.main:app', 8000),
]

procs = []
for module, port in services:
    p = subprocess.Popen(
        ['uv', 'run', 'uvicorn', module, '--host', '0.0.0.0', '--port', str(port)],
        env=os.environ.copy(),
        cwd=os.path.dirname(__file__)
    )
    procs.append(p)
    print(f'Started {module} on port {port}')
    time.sleep(1)

print('\nAll services started!')
print('Open http://localhost:8000')

# Handle shutdown
def handler(sig, frame):
    print('\nStopping services...')
    for p in procs:
        p.terminate()
    exit(0)

signal.signal(signal.SIGINT, handler)

# Keep running
while True:
    time.sleep(1)