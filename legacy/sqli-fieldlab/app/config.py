from __future__ import annotations

import os


class Config:
    DB_HOST = os.getenv("DB_HOST", "db")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("MYSQL_DATABASE", "sql_training")
    DB_USER = os.getenv("MYSQL_USER", "labapp")
    DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "labpass")

    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "5000"))
    APP_PUBLIC_PORT = int(os.getenv("APP_PUBLIC_PORT", "5050"))
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me-for-classroom")

    SQLALCHEMY_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
