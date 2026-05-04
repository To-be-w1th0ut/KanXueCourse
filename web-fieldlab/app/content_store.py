from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from config import Config
from content_seed import (
    AUTH_NOTES,
    AUTH_ORDERS,
    AUTH_TICKETS,
    AUTH_USERS,
    SSTI_TEMPLATES,
    SSTI_THEME_SNIPPETS,
    XSS_API_CARDS,
    XSS_BOOKMARKS,
    XSS_COMMENTS,
    XSS_MARKDOWN_NOTES,
    XSS_PROFILE,
    XSS_SVG_SNIPPETS,
)

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS xss_comments (comment_id INTEGER PRIMARY KEY AUTOINCREMENT, author TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS xss_profiles (profile_id INTEGER PRIMARY KEY CHECK (profile_id = 1), username TEXT NOT NULL, status_note TEXT NOT NULL, signature TEXT NOT NULL, updated_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS xss_bookmarks (bookmark_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, url TEXT NOT NULL, created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS xss_markdown_notes (note_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS xss_svg_snippets (snippet_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, svg_markup TEXT NOT NULL, created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS xss_api_cards (card_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, snippet TEXT NOT NULL, tag TEXT NOT NULL, created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS browser_events (event_id INTEGER PRIMARY KEY AUTOINCREMENT, lab_slug TEXT NOT NULL, message TEXT NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS ssti_templates (template_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS ssti_themes (theme_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS ssrf_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, lab_slug TEXT NOT NULL, target_url TEXT NOT NULL, outcome TEXT NOT NULL, preview TEXT NOT NULL, created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS auth_users (user_id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL, role TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS auth_orders (order_id INTEGER PRIMARY KEY, owner_user_id INTEGER NOT NULL, item_name TEXT NOT NULL, total_amount REAL NOT NULL, secret_note TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS auth_notes (note_id INTEGER PRIMARY KEY, owner_user_id INTEGER NOT NULL, body TEXT NOT NULL, updated_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS auth_tickets (ticket_id INTEGER PRIMARY KEY, owner_user_id INTEGER NOT NULL, subject TEXT NOT NULL, status TEXT NOT NULL, internal_note TEXT NOT NULL, updated_at TEXT NOT NULL)""",
]

RESET_GROUPS = {
    'xss': ['xss_comments', 'xss_profiles', 'xss_bookmarks', 'xss_markdown_notes', 'xss_svg_snippets', 'xss_api_cards', 'browser_events'],
    'ssti': ['ssti_templates', 'ssti_themes'],
    'ssrf': ['ssrf_logs'],
    'authz': ['auth_users', 'auth_orders', 'auth_notes', 'auth_tickets'],
    'events': ['browser_events'],
    'stored-comments': ['xss_comments'],
    'second-order-signature': ['xss_profiles'],
    'markdown-preview': ['xss_markdown_notes'],
    'svg-preview': ['xss_svg_snippets'],
    'url-bookmarks': ['xss_bookmarks'],
    'ssti-mail': ['ssti_templates'],
    'ssti-theme': ['ssti_themes'],
    'authz-orders': ['auth_orders'],
    'authz-notes': ['auth_notes'],
    'authz-tickets': ['auth_tickets'],
}


def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


def dict_factory(cursor: sqlite3.Cursor, row: tuple[Any, ...]) -> dict[str, Any]:
    return {column[0]: row[idx] for idx, column in enumerate(cursor.description)}


def connect() -> sqlite3.Connection:
    Config.ensure_paths()
    conn = sqlite3.connect(Config.CONTENT_DB_PATH)
    conn.row_factory = dict_factory
    return conn


def init_content_db(force: bool = False) -> None:
    Config.ensure_paths()
    with connect() as conn:
        for statement in SCHEMA:
            conn.execute(statement)
        if force or not Path(Config.CONTENT_DB_PATH).exists() or not fetch_scalar('SELECT COUNT(*) FROM auth_users', conn):
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
    for table in ['xss_comments','xss_profiles','xss_bookmarks','xss_markdown_notes','xss_svg_snippets','xss_api_cards','browser_events','ssti_templates','ssti_themes','ssrf_logs','auth_users','auth_orders','auth_notes','auth_tickets']:
        conn.execute(f'DELETE FROM {table}')
    now = utc_now()
    conn.executemany('INSERT INTO xss_comments (author, body, created_at) VALUES (:author, :body, :created_at)', [{**item, 'created_at': now} for item in XSS_COMMENTS])
    conn.execute('INSERT INTO xss_profiles (profile_id, username, status_note, signature, updated_at) VALUES (1, :username, :status_note, :signature, :updated_at)', {**XSS_PROFILE, 'updated_at': now})
    conn.executemany('INSERT INTO xss_bookmarks (title, url, created_at) VALUES (:title, :url, :created_at)', [{**item, 'created_at': now} for item in XSS_BOOKMARKS])
    conn.executemany('INSERT INTO xss_markdown_notes (title, body, created_at) VALUES (:title, :body, :created_at)', [{**item, 'created_at': now} for item in XSS_MARKDOWN_NOTES])
    conn.executemany('INSERT INTO xss_svg_snippets (title, svg_markup, created_at) VALUES (:title, :svg_markup, :created_at)', [{**item, 'created_at': now} for item in XSS_SVG_SNIPPETS])
    conn.executemany('INSERT INTO xss_api_cards (title, snippet, tag, created_at) VALUES (:title, :snippet, :tag, :created_at)', [{**item, 'created_at': now} for item in XSS_API_CARDS])
    conn.executemany('INSERT INTO ssti_templates (title, body, created_at) VALUES (:title, :body, :created_at)', [{**item, 'created_at': now} for item in SSTI_TEMPLATES])
    conn.executemany('INSERT INTO ssti_themes (name, body, created_at) VALUES (:name, :body, :created_at)', [{**item, 'created_at': now} for item in SSTI_THEME_SNIPPETS])
    conn.executemany('INSERT INTO auth_users (user_id, username, display_name, role) VALUES (:user_id, :username, :display_name, :role)', AUTH_USERS)
    conn.executemany('INSERT INTO auth_orders (order_id, owner_user_id, item_name, total_amount, secret_note) VALUES (:order_id, :owner_user_id, :item_name, :total_amount, :secret_note)', AUTH_ORDERS)
    conn.executemany('INSERT INTO auth_notes (note_id, owner_user_id, body, updated_at) VALUES (:note_id, :owner_user_id, :body, :updated_at)', [{**item, 'updated_at': now} for item in AUTH_NOTES])
    conn.executemany('INSERT INTO auth_tickets (ticket_id, owner_user_id, subject, status, internal_note, updated_at) VALUES (:ticket_id, :owner_user_id, :subject, :status, :internal_note, :updated_at)', [{**item, 'updated_at': now} for item in AUTH_TICKETS])


def query_all(sql: str, args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connect() as conn:
        return conn.execute(sql, args).fetchall()


def query_one(sql: str, args: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with connect() as conn:
        return conn.execute(sql, args).fetchone()


def execute(sql: str, args: tuple[Any, ...] = ()) -> int:
    with connect() as conn:
        cur = conn.execute(sql, args)
        conn.commit()
        return cur.rowcount


def reset_content(target: str) -> None:
    with connect() as conn:
        if target == 'all':
            seed_all(conn)
        else:
            for table in RESET_GROUPS.get(target, []):
                conn.execute(f'DELETE FROM {table}')
            if target in {'xss', 'stored-comments'}:
                conn.executemany('INSERT INTO xss_comments (author, body, created_at) VALUES (:author, :body, :created_at)', [{**item, 'created_at': utc_now()} for item in XSS_COMMENTS])
            if target in {'xss', 'second-order-signature'}:
                conn.execute('INSERT INTO xss_profiles (profile_id, username, status_note, signature, updated_at) VALUES (1, :username, :status_note, :signature, :updated_at)', {**XSS_PROFILE, 'updated_at': utc_now()})
            if target in {'xss', 'url-bookmarks'}:
                conn.executemany('INSERT INTO xss_bookmarks (title, url, created_at) VALUES (:title, :url, :created_at)', [{**item, 'created_at': utc_now()} for item in XSS_BOOKMARKS])
            if target in {'xss', 'markdown-preview'}:
                conn.executemany('INSERT INTO xss_markdown_notes (title, body, created_at) VALUES (:title, :body, :created_at)', [{**item, 'created_at': utc_now()} for item in XSS_MARKDOWN_NOTES])
            if target in {'xss', 'svg-preview'}:
                conn.executemany('INSERT INTO xss_svg_snippets (title, svg_markup, created_at) VALUES (:title, :svg_markup, :created_at)', [{**item, 'created_at': utc_now()} for item in XSS_SVG_SNIPPETS])
            if target == 'xss':
                conn.executemany('INSERT INTO xss_api_cards (title, snippet, tag, created_at) VALUES (:title, :snippet, :tag, :created_at)', [{**item, 'created_at': utc_now()} for item in XSS_API_CARDS])
            if target in {'ssti', 'ssti-mail'}:
                conn.executemany('INSERT INTO ssti_templates (title, body, created_at) VALUES (:title, :body, :created_at)', [{**item, 'created_at': utc_now()} for item in SSTI_TEMPLATES])
            if target in {'ssti', 'ssti-theme'}:
                conn.executemany('INSERT INTO ssti_themes (name, body, created_at) VALUES (:name, :body, :created_at)', [{**item, 'created_at': utc_now()} for item in SSTI_THEME_SNIPPETS])
            if target in {'authz', 'authz-orders'}:
                conn.executemany('INSERT INTO auth_orders (order_id, owner_user_id, item_name, total_amount, secret_note) VALUES (:order_id, :owner_user_id, :item_name, :total_amount, :secret_note)', AUTH_ORDERS)
            if target in {'authz', 'authz-notes'}:
                conn.executemany('INSERT INTO auth_notes (note_id, owner_user_id, body, updated_at) VALUES (:note_id, :owner_user_id, :body, :updated_at)', [{**item, 'updated_at': utc_now()} for item in AUTH_NOTES])
            if target in {'authz', 'authz-tickets'}:
                conn.executemany('INSERT INTO auth_tickets (ticket_id, owner_user_id, subject, status, internal_note, updated_at) VALUES (:ticket_id, :owner_user_id, :subject, :status, :internal_note, :updated_at)', [{**item, 'updated_at': utc_now()} for item in AUTH_TICKETS])
            if target == 'authz':
                conn.executemany('INSERT INTO auth_users (user_id, username, display_name, role) VALUES (:user_id, :username, :display_name, :role)', AUTH_USERS)
        conn.commit()
