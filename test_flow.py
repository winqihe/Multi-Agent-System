#!/usr/bin/env python3
"""Test complete course generation flow."""

import httpx
import json
import os

# Disable proxy
for proxy_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(proxy_var, None)

print('Testing complete course generation flow...')
print('=' * 50)

# Test Orchestrator run_stream
print('\nCalling Orchestrator...')
try:
    with httpx.Client(timeout=180.0) as client:
        with client.stream('POST', 'http://127.0.0.1:8004/run_stream', params={'topic': 'Python基础编程'}) as response:
            print(f'Status: {response.status_code}')
            for line in response.iter_lines():
                if line:
                    try:
                        event = json.loads(line)
                        if event.get('type') == 'progress':
                            print(f'[Progress] {event.get("agent")}: {event.get("message")}')
                        elif event.get('type') == 'result':
                            print('\n' + '=' * 50)
                            print('Course Generated!')
                            print('=' * 50)
                            course = event.get('course', '')
                            print(course[:800] + '...' if len(course) > 800 else course)
                        elif event.get('type') == 'error':
                            print(f'[Error] {event.get("error")}')
                    except json.JSONDecodeError:
                        print(f'Raw: {line}')
except Exception as e:
    print(f'Exception: {e}')