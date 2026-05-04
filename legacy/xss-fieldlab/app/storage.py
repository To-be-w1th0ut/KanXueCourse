from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from config import Config
from seed_data import (
    SEED_API_CARDS,
    SEED_BOOKMARKS,
    SEED_COMMENTS,
    SEED_MARKDOWN_NOTES,
    SEED_PROFILE,
    SEED_SVG_SNIPPETS,
)

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS comments (
      comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
      author TEXT NOT NULL,
      body TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS profiles (
      profile_id INTEGER PRIMARY KEY CHECK (profile_id = 1),
      username TEXT NOT NULL,
      status_note TEXT NOT NULL,
      signature TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS bookmarks (
      bookmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      url TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS markdown_notes (
      note_id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      body TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS svg_snippets (
      snippet_id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      svg_markup TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS api_cards (
      card_id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      snippet TEXT NOT NULL,
      tag TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS lab_events (
      event_id INTEGER PRIMARY KEY AUTOINCREMENT,
      lab_slug TEXT NOT NULL,
      message TEXT NOT NULL,
      source TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """,
]

LAB_RESET_MAP = {
    "stored-comments": ["comments"],
    "second-order-signature": ["profiles"],
    "markdown-preview": ["markdown_notes"],
    "svg-preview": ["svg_snippets"],
    "url-bookmarks": ["bookmarks"],
    "events": ["lab_events"],
}


def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def dict_factory(cursor: sqlite3.Cursor, row: tuple[Any, ...]) -> dict[str, Any]:
    return {column[0]: row[idx] for idx, column in enumerate(cursor.description)}


def connect() -> sqlite3.Connection:
    Config.ensure_paths()
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = dict_factory
    return conn


def init_db(force: bool = False) -> None:
    Config.ensure_paths()
    db_file = Path(Config.DB_PATH)
    with connect() as conn:
        cursor = conn.cursor()
        for statement in SCHEMA:
            cursor.execute(statement)
        if force or not db_file.exists() or not fetch_scalar("SELECT COUNT(*) FROM comments", conn):
            seed_all(conn)
        conn.commit()


def fetch_scalar(sql: str, conn: sqlite3.Connection | None = None, args: tuple[Any, ...] = ()) -> Any:
    owns = conn is None
    connection = conn or connect()
    try:
        row = connection.execute(sql, args).fetchone()
        return next(iter(row.values())) if row else None
    finally:
        if owns:
            connection.close()


def seed_all(conn: sqlite3.Connection) -> None:
    for table in ["comments", "profiles", "bookmarks", "markdown_notes", "svg_snippets", "api_cards", "lab_events"]:
        conn.execute(f"DELETE FROM {table}")
    now = utc_now()
    conn.executemany(
        "INSERT INTO comments (author, body, created_at) VALUES (:author, :body, :created_at)",
        [{**item, "created_at": now} for item in SEED_COMMENTS],
    )
    conn.execute(
        "INSERT INTO profiles (profile_id, username, status_note, signature, updated_at) VALUES (1, :username, :status_note, :signature, :updated_at)",
        {**SEED_PROFILE, "updated_at": now},
    )
    conn.executemany(
        "INSERT INTO bookmarks (title, url, created_at) VALUES (:title, :url, :created_at)",
        [{**item, "created_at": now} for item in SEED_BOOKMARKS],
    )
    conn.executemany(
        "INSERT INTO markdown_notes (title, body, created_at) VALUES (:title, :body, :created_at)",
        [{**item, "created_at": now} for item in SEED_MARKDOWN_NOTES],
    )
    conn.executemany(
        "INSERT INTO svg_snippets (title, svg_markup, created_at) VALUES (:title, :svg_markup, :created_at)",
        [{**item, "created_at": now} for item in SEED_SVG_SNIPPETS],
    )
    conn.executemany(
        "INSERT INTO api_cards (title, snippet, tag, created_at) VALUES (:title, :snippet, :tag, :created_at)",
        [{**item, "created_at": now} for item in SEED_API_CARDS],
    )


def query_all(sql: str, args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connect() as conn:
        return conn.execute(sql, args).fetchall()


def query_one(sql: str, args: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with connect() as conn:
        return conn.execute(sql, args).fetchone()


def execute(sql: str, args: tuple[Any, ...] = ()) -> int:
    with connect() as conn:
        cursor = conn.execute(sql, args)
        conn.commit()
        return cursor.rowcount


def reset_target(target: str) -> None:
    with connect() as conn:
        if target == "all":
            seed_all(conn)
        else:
            for table in LAB_RESET_MAP.get(target, []):
                conn.execute(f"DELETE FROM {table}")
            if target == "stored-comments":
                conn.executemany(
                    "INSERT INTO comments (author, body, created_at) VALUES (:author, :body, :created_at)",
                    [{**item, "created_at": utc_now()} for item in SEED_COMMENTS],
                )
            elif target == "second-order-signature":
                conn.execute(
                    "INSERT INTO profiles (profile_id, username, status_note, signature, updated_at) VALUES (1, :username, :status_note, :signature, :updated_at)",
                    {**SEED_PROFILE, "updated_at": utc_now()},
                )
            elif target == "markdown-preview":
                conn.executemany(
                    "INSERT INTO markdown_notes (title, body, created_at) VALUES (:title, :body, :created_at)",
                    [{**item, "created_at": utc_now()} for item in SEED_MARKDOWN_NOTES],
                )
            elif target == "svg-preview":
                conn.executemany(
                    "INSERT INTO svg_snippets (title, svg_markup, created_at) VALUES (:title, :svg_markup, :created_at)",
                    [{**item, "created_at": utc_now()} for item in SEED_SVG_SNIPPETS],
                )
            elif target == "url-bookmarks":
                conn.executemany(
                    "INSERT INTO bookmarks (title, url, created_at) VALUES (:title, :url, :created_at)",
                    [{**item, "created_at": utc_now()} for item in SEED_BOOKMARKS],
                )
        conn.commit()
