#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-all}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 app/reset_db.py "$TARGET"
