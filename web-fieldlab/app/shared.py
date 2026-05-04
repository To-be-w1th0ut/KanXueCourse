from __future__ import annotations

from flask import request


def current_mode() -> str:
    return 'safe' if request.args.get('mode') == 'safe' else 'vuln'
