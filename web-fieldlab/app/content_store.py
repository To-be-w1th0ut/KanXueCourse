from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from config import Config
from content_seed import (
    AUTH_NOTES,
    AUTH_ORDERS,
    AUTH_REPORTS,
    AUTH_TICKETS,
    AUTH_USERS,
    CSRF_ACCOUNTS,
    CSRF_TRANSFER_LOGS,
    INJECTION_AUDIT_LOG,
    INJECTION_SNIPPETS,
    JSONP_PROFILES,
    PAYMENT_COUPONS,
    PAYMENT_ORDERS,
    PAYMENT_PRODUCTS,
    PAYMENT_WALLETS,
    RACE_COUPONS,
    RACE_INVENTORY,
    RACE_SEATS,
    RACE_WALLETS,
    SSTI_TEMPLATES,
    SSTI_THEME_SNIPPETS,
    UPLOAD_BANNER_HTML,
    UPLOAD_SEEDS,
    XXE_DOCUMENTS,
    XXE_SECRET_TEXT,
    XSS_API_CARDS,
    XSS_BOOKMARKS,
    XSS_COMMENTS,
    XSS_MARKDOWN_NOTES,
    XSS_PROFILE,
    XSS_SVG_SNIPPETS,
)

SCHEMA = [
    "CREATE TABLE IF NOT EXISTS xss_comments (comment_id INTEGER PRIMARY KEY AUTOINCREMENT, author TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS xss_profiles (profile_id INTEGER PRIMARY KEY CHECK (profile_id = 1), username TEXT NOT NULL, status_note TEXT NOT NULL, signature TEXT NOT NULL, updated_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS xss_bookmarks (bookmark_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, url TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS xss_markdown_notes (note_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS xss_svg_snippets (snippet_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, svg_markup TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS xss_api_cards (card_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, snippet TEXT NOT NULL, tag TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS browser_events (event_id INTEGER PRIMARY KEY AUTOINCREMENT, lab_slug TEXT NOT NULL, message TEXT NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS ssti_templates (template_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS ssti_themes (theme_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS ssrf_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, lab_slug TEXT NOT NULL, target_url TEXT NOT NULL, outcome TEXT NOT NULL, preview TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS auth_users (user_id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL, role TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS auth_orders (order_id INTEGER PRIMARY KEY, owner_user_id INTEGER NOT NULL, item_name TEXT NOT NULL, total_amount REAL NOT NULL, secret_note TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS auth_notes (note_id INTEGER PRIMARY KEY, owner_user_id INTEGER NOT NULL, body TEXT NOT NULL, updated_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS auth_tickets (ticket_id INTEGER PRIMARY KEY, owner_user_id INTEGER NOT NULL, subject TEXT NOT NULL, status TEXT NOT NULL, internal_note TEXT NOT NULL, updated_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS auth_reports (report_id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS upload_entries (upload_id INTEGER PRIMARY KEY AUTOINCREMENT, lab_slug TEXT NOT NULL, original_name TEXT NOT NULL, stored_name TEXT NOT NULL, declared_type TEXT NOT NULL, stored_path TEXT NOT NULL, note TEXT NOT NULL, is_public INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS payment_products (product_id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS payment_wallets (owner_label TEXT PRIMARY KEY, balance REAL NOT NULL, credits INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS payment_coupons (code TEXT PRIMARY KEY, discount_amount REAL NOT NULL, remaining_uses INTEGER NOT NULL, active INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS payment_orders (order_id INTEGER PRIMARY KEY AUTOINCREMENT, order_ref TEXT NOT NULL UNIQUE, owner_label TEXT NOT NULL, product_name TEXT NOT NULL, expected_amount REAL NOT NULL, paid_amount REAL NOT NULL, status TEXT NOT NULL, note TEXT NOT NULL, callback_count INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS injection_snippets (snippet_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS xxe_documents (doc_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS jsonp_profiles (username TEXT PRIMARY KEY, email TEXT NOT NULL, role TEXT NOT NULL, private_note TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS race_coupons (code TEXT PRIMARY KEY, remaining_uses INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS race_inventory (sku TEXT PRIMARY KEY, stock INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS race_wallets (owner TEXT PRIMARY KEY, balance REAL NOT NULL)",
    "CREATE TABLE IF NOT EXISTS race_seats (event_name TEXT PRIMARY KEY, remaining INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS race_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, lab_slug TEXT NOT NULL, attempts INTEGER NOT NULL, success_count INTEGER NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS csrf_accounts (username TEXT PRIMARY KEY, balance REAL NOT NULL, email_pref TEXT NOT NULL, mfa_enabled INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS csrf_transfer_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, from_user TEXT NOT NULL, to_user TEXT NOT NULL, amount REAL NOT NULL, note TEXT NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL)",
]

RESET_GROUPS = {
    'xss': ['xss_comments', 'xss_profiles', 'xss_bookmarks', 'xss_markdown_notes', 'xss_svg_snippets', 'xss_api_cards', 'browser_events'],
    'ssti': ['ssti_templates', 'ssti_themes'],
    'ssrf': ['ssrf_logs'],
    'authz': ['auth_users', 'auth_orders', 'auth_notes', 'auth_tickets', 'auth_reports'],
    'upload': ['upload_entries'],
    'payment': ['payment_products', 'payment_wallets', 'payment_coupons', 'payment_orders'],
    'injection': ['injection_snippets'],
    'xxe': ['xxe_documents'],
    'jsonp': ['jsonp_profiles'],
    'race': ['race_coupons', 'race_inventory', 'race_wallets', 'race_seats', 'race_logs'],
    'csrf': ['csrf_accounts', 'csrf_transfer_logs'],
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
    'upload-public': ['upload_entries'],
    'payment-wallet': ['payment_wallets'],
    'payment-coupons': ['payment_coupons'],
    'payment-orders': ['payment_orders'],
    'injection-snippets': ['injection_snippets'],
    'xxe-docs': ['xxe_documents'],
    'jsonp-profiles': ['jsonp_profiles'],
    'race-coupons': ['race_coupons', 'race_logs'],
    'race-inventory': ['race_inventory', 'race_logs'],
    'race-wallets': ['race_wallets', 'race_logs'],
    'race-seats': ['race_seats', 'race_logs'],
    'csrf-wallets': ['csrf_accounts'],
    'csrf-logs': ['csrf_transfer_logs'],
}


def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


def data_root() -> Path:
    root = Path(Config.CONTENT_DB_PATH).parent
    root.mkdir(parents=True, exist_ok=True)
    return root


def uploads_root() -> Path:
    root = data_root() / 'uploads'
    (root / 'public').mkdir(parents=True, exist_ok=True)
    (root / 'private').mkdir(parents=True, exist_ok=True)
    (root / 'scratch').mkdir(parents=True, exist_ok=True)
    return root


def write_seed_files() -> None:
    root = data_root()
    uploads = uploads_root()
    (root / 'upload_banner.html').write_text(UPLOAD_BANNER_HTML)
    (root / 'cmd_audit.log').write_text(INJECTION_AUDIT_LOG)
    (root / 'xxe-secret.txt').write_text(XXE_SECRET_TEXT)
    (uploads / 'public' / 'welcome.txt').write_text('Welcome to Unified FieldLab uploads.')


def wipe_upload_files() -> None:
    uploads = uploads_root()
    for child in uploads.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
            child.mkdir(parents=True, exist_ok=True)
        else:
            child.unlink(missing_ok=True)
    write_seed_files()


def dict_factory(cursor: sqlite3.Cursor, row: tuple[Any, ...]) -> dict[str, Any]:
    return {column[0]: row[idx] for idx, column in enumerate(cursor.description)}


def connect() -> sqlite3.Connection:
    Config.ensure_paths()
    conn = sqlite3.connect(Config.CONTENT_DB_PATH, check_same_thread=False)
    conn.row_factory = dict_factory
    return conn


def init_content_db(force: bool = False) -> None:
    Config.ensure_paths()
    db_existed = Path(Config.CONTENT_DB_PATH).exists()
    with connect() as conn:
        for statement in SCHEMA:
            conn.execute(statement)
        needs_seed = force or not db_existed
        for probe in ['SELECT COUNT(*) FROM auth_users', 'SELECT COUNT(*) FROM payment_products', 'SELECT COUNT(*) FROM jsonp_profiles', 'SELECT COUNT(*) FROM race_coupons', 'SELECT COUNT(*) FROM upload_entries', 'SELECT COUNT(*) FROM csrf_accounts']:
            if not fetch_scalar(probe, conn):
                needs_seed = True
                break
        if needs_seed:
            seed_all(conn)
        conn.commit()
    write_seed_files()


def fetch_scalar(sql: str, conn: sqlite3.Connection | None = None, args: tuple[Any, ...] = ()) -> Any:
    owns = conn is None
    connection = conn or connect()
    try:
        row = connection.execute(sql, args).fetchone()
        return next(iter(row.values())) if row else None
    finally:
        if owns:
            connection.close()


def _seed_tables(conn: sqlite3.Connection, now: str) -> None:
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
    conn.executemany('INSERT INTO auth_reports (report_id, title, body) VALUES (:report_id, :title, :body)', AUTH_REPORTS)
    conn.executemany('INSERT INTO upload_entries (lab_slug, original_name, stored_name, declared_type, stored_path, note, is_public, created_at) VALUES (:lab_slug, :original_name, :stored_name, :declared_type, :stored_path, :note, :is_public, :created_at)', [{**item, 'created_at': now} for item in UPLOAD_SEEDS])
    conn.executemany('INSERT INTO payment_products (product_id, name, price, stock) VALUES (:product_id, :name, :price, :stock)', PAYMENT_PRODUCTS)
    conn.executemany('INSERT INTO payment_wallets (owner_label, balance, credits) VALUES (:owner_label, :balance, :credits)', PAYMENT_WALLETS)
    conn.executemany('INSERT INTO payment_coupons (code, discount_amount, remaining_uses, active) VALUES (:code, :discount_amount, :remaining_uses, :active)', PAYMENT_COUPONS)
    conn.executemany('INSERT INTO payment_orders (order_ref, owner_label, product_name, expected_amount, paid_amount, status, note, callback_count, created_at) VALUES (:order_ref, :owner_label, :product_name, :expected_amount, :paid_amount, :status, :note, :callback_count, :created_at)', [{**item, 'created_at': now} for item in PAYMENT_ORDERS])
    conn.executemany('INSERT INTO injection_snippets (title, body, created_at) VALUES (:title, :body, :created_at)', [{**item, 'created_at': now} for item in INJECTION_SNIPPETS])
    conn.executemany('INSERT INTO xxe_documents (title, body, created_at) VALUES (:title, :body, :created_at)', [{**item, 'created_at': now} for item in XXE_DOCUMENTS])
    conn.executemany('INSERT INTO jsonp_profiles (username, email, role, private_note) VALUES (:username, :email, :role, :private_note)', JSONP_PROFILES)
    conn.executemany('INSERT INTO race_coupons (code, remaining_uses) VALUES (:code, :remaining_uses)', RACE_COUPONS)
    conn.executemany('INSERT INTO race_inventory (sku, stock) VALUES (:sku, :stock)', RACE_INVENTORY)
    conn.executemany('INSERT INTO race_wallets (owner, balance) VALUES (:owner, :balance)', RACE_WALLETS)
    conn.executemany('INSERT INTO race_seats (event_name, remaining) VALUES (:event_name, :remaining)', RACE_SEATS)
    conn.executemany('INSERT INTO csrf_accounts (username, balance, email_pref, mfa_enabled) VALUES (:username, :balance, :email_pref, :mfa_enabled)', CSRF_ACCOUNTS)
    conn.executemany('INSERT INTO csrf_transfer_logs (from_user, to_user, amount, note, source, created_at) VALUES (:from_user, :to_user, :amount, :note, :source, :created_at)', [{**item, 'created_at': now} for item in CSRF_TRANSFER_LOGS])


def seed_all(conn: sqlite3.Connection) -> None:
    for table in ['xss_comments','xss_profiles','xss_bookmarks','xss_markdown_notes','xss_svg_snippets','xss_api_cards','browser_events','ssti_templates','ssti_themes','ssrf_logs','auth_users','auth_orders','auth_notes','auth_tickets','auth_reports','upload_entries','payment_products','payment_wallets','payment_coupons','payment_orders','injection_snippets','xxe_documents','jsonp_profiles','race_coupons','race_inventory','race_wallets','race_seats','race_logs','csrf_accounts','csrf_transfer_logs']:
        conn.execute(f'DELETE FROM {table}')
    wipe_upload_files()
    _seed_tables(conn, utc_now())


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
            now = utc_now()
            if target in {'xss', 'stored-comments'}:
                conn.executemany('INSERT INTO xss_comments (author, body, created_at) VALUES (:author, :body, :created_at)', [{**item, 'created_at': now} for item in XSS_COMMENTS])
            if target in {'xss', 'second-order-signature'}:
                conn.execute('INSERT INTO xss_profiles (profile_id, username, status_note, signature, updated_at) VALUES (1, :username, :status_note, :signature, :updated_at)', {**XSS_PROFILE, 'updated_at': now})
            if target in {'xss', 'url-bookmarks'}:
                conn.executemany('INSERT INTO xss_bookmarks (title, url, created_at) VALUES (:title, :url, :created_at)', [{**item, 'created_at': now} for item in XSS_BOOKMARKS])
            if target in {'xss', 'markdown-preview'}:
                conn.executemany('INSERT INTO xss_markdown_notes (title, body, created_at) VALUES (:title, :body, :created_at)', [{**item, 'created_at': now} for item in XSS_MARKDOWN_NOTES])
            if target in {'xss', 'svg-preview'}:
                conn.executemany('INSERT INTO xss_svg_snippets (title, svg_markup, created_at) VALUES (:title, :svg_markup, :created_at)', [{**item, 'created_at': now} for item in XSS_SVG_SNIPPETS])
            if target == 'xss':
                conn.executemany('INSERT INTO xss_api_cards (title, snippet, tag, created_at) VALUES (:title, :snippet, :tag, :created_at)', [{**item, 'created_at': now} for item in XSS_API_CARDS])
            if target in {'ssti', 'ssti-mail'}:
                conn.executemany('INSERT INTO ssti_templates (title, body, created_at) VALUES (:title, :body, :created_at)', [{**item, 'created_at': now} for item in SSTI_TEMPLATES])
            if target in {'ssti', 'ssti-theme'}:
                conn.executemany('INSERT INTO ssti_themes (name, body, created_at) VALUES (:name, :body, :created_at)', [{**item, 'created_at': now} for item in SSTI_THEME_SNIPPETS])
            if target in {'authz', 'authz-orders'}:
                conn.executemany('INSERT INTO auth_orders (order_id, owner_user_id, item_name, total_amount, secret_note) VALUES (:order_id, :owner_user_id, :item_name, :total_amount, :secret_note)', AUTH_ORDERS)
            if target in {'authz', 'authz-notes'}:
                conn.executemany('INSERT INTO auth_notes (note_id, owner_user_id, body, updated_at) VALUES (:note_id, :owner_user_id, :body, :updated_at)', [{**item, 'updated_at': now} for item in AUTH_NOTES])
            if target in {'authz', 'authz-tickets'}:
                conn.executemany('INSERT INTO auth_tickets (ticket_id, owner_user_id, subject, status, internal_note, updated_at) VALUES (:ticket_id, :owner_user_id, :subject, :status, :internal_note, :updated_at)', [{**item, 'updated_at': now} for item in AUTH_TICKETS])
            if target == 'authz':
                conn.executemany('INSERT INTO auth_users (user_id, username, display_name, role) VALUES (:user_id, :username, :display_name, :role)', AUTH_USERS)
                conn.executemany('INSERT INTO auth_reports (report_id, title, body) VALUES (:report_id, :title, :body)', AUTH_REPORTS)
            if target in {'upload', 'upload-public'}:
                wipe_upload_files()
                conn.executemany('INSERT INTO upload_entries (lab_slug, original_name, stored_name, declared_type, stored_path, note, is_public, created_at) VALUES (:lab_slug, :original_name, :stored_name, :declared_type, :stored_path, :note, :is_public, :created_at)', [{**item, 'created_at': now} for item in UPLOAD_SEEDS])
            if target == 'payment':
                conn.executemany('INSERT INTO payment_products (product_id, name, price, stock) VALUES (:product_id, :name, :price, :stock)', PAYMENT_PRODUCTS)
                conn.executemany('INSERT INTO payment_wallets (owner_label, balance, credits) VALUES (:owner_label, :balance, :credits)', PAYMENT_WALLETS)
                conn.executemany('INSERT INTO payment_coupons (code, discount_amount, remaining_uses, active) VALUES (:code, :discount_amount, :remaining_uses, :active)', PAYMENT_COUPONS)
                conn.executemany('INSERT INTO payment_orders (order_ref, owner_label, product_name, expected_amount, paid_amount, status, note, callback_count, created_at) VALUES (:order_ref, :owner_label, :product_name, :expected_amount, :paid_amount, :status, :note, :callback_count, :created_at)', [{**item, 'created_at': now} for item in PAYMENT_ORDERS])
            if target == 'payment-wallet':
                conn.executemany('INSERT INTO payment_wallets (owner_label, balance, credits) VALUES (:owner_label, :balance, :credits)', PAYMENT_WALLETS)
            if target == 'payment-coupons':
                conn.executemany('INSERT INTO payment_coupons (code, discount_amount, remaining_uses, active) VALUES (:code, :discount_amount, :remaining_uses, :active)', PAYMENT_COUPONS)
            if target == 'payment-orders':
                conn.executemany('INSERT INTO payment_orders (order_ref, owner_label, product_name, expected_amount, paid_amount, status, note, callback_count, created_at) VALUES (:order_ref, :owner_label, :product_name, :expected_amount, :paid_amount, :status, :note, :callback_count, :created_at)', [{**item, 'created_at': now} for item in PAYMENT_ORDERS])
            if target in {'injection', 'injection-snippets'}:
                (data_root() / 'cmd_audit.log').write_text(INJECTION_AUDIT_LOG)
                conn.executemany('INSERT INTO injection_snippets (title, body, created_at) VALUES (:title, :body, :created_at)', [{**item, 'created_at': now} for item in INJECTION_SNIPPETS])
            if target in {'xxe', 'xxe-docs'}:
                (data_root() / 'xxe-secret.txt').write_text(XXE_SECRET_TEXT)
                conn.executemany('INSERT INTO xxe_documents (title, body, created_at) VALUES (:title, :body, :created_at)', [{**item, 'created_at': now} for item in XXE_DOCUMENTS])
            if target in {'jsonp', 'jsonp-profiles'}:
                conn.executemany('INSERT INTO jsonp_profiles (username, email, role, private_note) VALUES (:username, :email, :role, :private_note)', JSONP_PROFILES)
            if target in {'race', 'race-coupons'}:
                conn.executemany('INSERT INTO race_coupons (code, remaining_uses) VALUES (:code, :remaining_uses)', RACE_COUPONS)
            if target in {'race', 'race-inventory'}:
                conn.executemany('INSERT INTO race_inventory (sku, stock) VALUES (:sku, :stock)', RACE_INVENTORY)
            if target in {'race', 'race-wallets'}:
                conn.executemany('INSERT INTO race_wallets (owner, balance) VALUES (:owner, :balance)', RACE_WALLETS)
            if target in {'race', 'race-seats'}:
                conn.executemany('INSERT INTO race_seats (event_name, remaining) VALUES (:event_name, :remaining)', RACE_SEATS)
            if target in {'csrf', 'csrf-wallets'}:
                conn.executemany('INSERT INTO csrf_accounts (username, balance, email_pref, mfa_enabled) VALUES (:username, :balance, :email_pref, :mfa_enabled)', CSRF_ACCOUNTS)
            if target in {'csrf', 'csrf-logs'}:
                conn.executemany('INSERT INTO csrf_transfer_logs (from_user, to_user, amount, note, source, created_at) VALUES (:from_user, :to_user, :amount, :note, :source, :created_at)', [{**item, 'created_at': now} for item in CSRF_TRANSFER_LOGS])
        conn.commit()
