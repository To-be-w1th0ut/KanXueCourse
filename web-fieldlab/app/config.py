from __future__ import annotations

import os
from pathlib import Path


class Config:
    DB_HOST = os.getenv('DB_HOST', 'db')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_NAME = os.getenv('MYSQL_DATABASE', 'sql_training')
    DB_USER = os.getenv('MYSQL_USER', 'labapp')
    DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'labpass')

    APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
    APP_PORT = int(os.getenv('APP_PORT', '5000'))
    APP_PUBLIC_PORT = int(os.getenv('APP_PUBLIC_PORT', '5070'))
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'change-me-for-classroom')

    CONTENT_DB_PATH = os.getenv('CONTENT_DB_PATH', '/app/data/content.db')
    SSRF_INTERNAL_BASE = os.getenv('SSRF_INTERNAL_BASE', 'http://intranet:7001')

    SQLALCHEMY_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )

    @classmethod
    def ensure_paths(cls) -> None:
        Path(cls.CONTENT_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
