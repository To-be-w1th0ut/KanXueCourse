#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-all}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

case "$TARGET" in
  all)
    docker compose down -v
    docker compose up -d --build
    ;;
  sqli)
    docker compose exec -T db mariadb -uroot -p"${MYSQL_ROOT_PASSWORD:-labroot}" sql_training < "$ROOT/db/00_schema.sql"
    docker compose exec -T db mariadb -uroot -p"${MYSQL_ROOT_PASSWORD:-labroot}" sql_training < "$ROOT/db/01_seed.sql"
    ;;
  sqli-grades)
    docker compose exec -T db mariadb -uroot -p"${MYSQL_ROOT_PASSWORD:-labroot}" sql_training < "$ROOT/db/resets/reset_grades.sql"
    ;;
  sqli-filters)
    docker compose exec -T db mariadb -uroot -p"${MYSQL_ROOT_PASSWORD:-labroot}" sql_training < "$ROOT/db/resets/reset_saved_filters.sql"
    ;;
  sqli-register)
    docker compose exec -T db mariadb -uroot -p"${MYSQL_ROOT_PASSWORD:-labroot}" sql_training < "$ROOT/db/resets/reset_register_users.sql"
    ;;
  sqli-cleanup)
    docker compose exec -T db mariadb -uroot -p"${MYSQL_ROOT_PASSWORD:-labroot}" sql_training < "$ROOT/db/resets/reset_cleanup_jobs.sql"
    ;;
  sqli-audit)
    docker compose exec -T db mariadb -uroot -p"${MYSQL_ROOT_PASSWORD:-labroot}" sql_training < "$ROOT/db/resets/reset_audit_logs.sql"
    ;;
  sqli-theme)
    docker compose exec -T db mariadb -uroot -p"${MYSQL_ROOT_PASSWORD:-labroot}" sql_training < "$ROOT/db/resets/reset_theme_prefs.sql"
    ;;
  sqli-fileio)
    docker compose exec -T db mariadb -uroot -p"${MYSQL_ROOT_PASSWORD:-labroot}" sql_training < "$ROOT/db/resets/reset_dnslog.sql"
    docker compose exec -T web sh -c 'rm -rf /tmp/lab/* 2>/dev/null || true'
    ;;
  sqli-dnslog)
    docker compose exec -T db mariadb -uroot -p"${MYSQL_ROOT_PASSWORD:-labroot}" sql_training < "$ROOT/db/resets/reset_dnslog.sql"
    ;;
  xss|ssti|ssrf|authz|csrf|upload|payment|injection|xxe|jsonp|race|events|stored-comments|second-order-signature|markdown-preview|svg-preview|url-bookmarks|xss-mxss|ssti-mail|ssti-theme|authz-orders|authz-notes|authz-tickets|authz-invoices|authz-messages|authz-prefs|upload-public|payment-wallet|payment-coupons|payment-orders|payment-flash|injection-snippets|race-double-spend|xxe-docs|jsonp-profiles|race-coupons|race-inventory|race-wallets|race-seats|csrf-wallets|csrf-logs)
    CONTENT_DB_PATH="$ROOT/app/data/content.db" python3 app/reset_content.py "$TARGET"
    ;;
  *)
    echo "用法: ./scripts/reset_lab.sh [all|sqli|sqli-grades|sqli-filters|sqli-register|sqli-cleanup|sqli-audit|sqli-theme|sqli-fileio|sqli-dnslog|xss|ssti|ssrf|authz|csrf|upload|payment|injection|xxe|jsonp|race|events|stored-comments|second-order-signature|markdown-preview|svg-preview|url-bookmarks|xss-mxss|ssti-mail|ssti-theme|authz-orders|authz-notes|authz-tickets|authz-invoices|authz-messages|authz-prefs|upload-public|payment-wallet|payment-coupons|payment-orders|payment-flash|injection-snippets|race-double-spend|xxe-docs|jsonp-profiles|race-coupons|race-inventory|race-wallets|race-seats|csrf-wallets|csrf-logs]" >&2
    exit 1
    ;;
esac
