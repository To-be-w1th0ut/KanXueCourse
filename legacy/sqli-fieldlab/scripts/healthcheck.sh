#!/usr/bin/env bash
set -euo pipefail
PORT="${HOST_WEB_PORT:-5050}"
curl -fsS "http://127.0.0.1:${PORT}/healthz" | python3 -m json.tool
