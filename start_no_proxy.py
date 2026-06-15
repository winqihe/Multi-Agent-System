#!/usr/bin/env python3
"""Start all services without proxy, with log files."""

import os
import subprocess
import time
import signal

# Disable proxy
for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(proxy_var, None)

# Load environment from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
with open(env_path) as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            key, val = line.strip().split('=', 1)
            os.environ[key] = val

print("Environment loaded (no proxy):")
print(f"  XIAOMI_API_BASE: {os.environ.get('XIAOMI_API_BASE')}")
print(f"  XIAOMI_MODEL: {os.environ.get('XIAOMI_MODEL')}")

# Start all services
services = [
    ('agents.researcher.main:app', 8001),
    ('agents.judge.main:app', 8002),
    ('agents.content_builder.main:app', 8003),
    ('agents.orchestrator.main:app', 8004),
    ('app.main:app', 8000),
]

log_dir = '/tmp/svc_logs'
os.makedirs(log_dir, exist_ok=True)

procs = []
for module, port in services:
    log_file = open(os.path.join(log_dir, f'port_{port}.log'), 'w')
    p = subprocess.Popen(
        ['uv', 'run', 'uvicorn', module, '--host', '0.0.0.0', '--port', str(port)],
        env=os.environ.copy(),
        cwd=os.path.dirname(__file__),
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    procs.append((p, log_file))
    print(f'Started {module} on port {port} (log: {log_dir}/port_{port}.log)')
    time.sleep(1)

print('\nAll services started!')
print('Open http://localhost:8000')
print(f'Logs in {log_dir}/')

# Handle shutdown
def handler(sig, frame):
    print('\nStopping services...')
    for p, f in procs:
        p.terminate()
        f.close()
    exit(0)

signal.signal(signal.SIGINT, handler)

# Keep running
while True:
    time.sleep(1)
