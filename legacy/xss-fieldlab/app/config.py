from __future__ import annotations

import os
from pathlib import Path


class Config:
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "5000"))
    APP_PUBLIC_PORT = int(os.getenv("APP_PUBLIC_PORT", "5060"))
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me-for-classroom")
    DB_PATH = os.getenv("DB_PATH", "/app/data/fieldlab.db")

    @classmethod
    def ensure_paths(cls) -> None:
        Path(cls.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
