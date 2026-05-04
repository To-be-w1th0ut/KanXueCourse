#!/usr/bin/env bash
set -euo pipefail
export PORT="${HOST_WEB_PORT:-5070}"
python3 - <<'PY'
import json, os, urllib.request
port = os.environ.get('PORT', '5070')
with urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz', timeout=5) as resp:
    print(json.dumps(json.loads(resp.read().decode()), ensure_ascii=False, indent=2))
PY
