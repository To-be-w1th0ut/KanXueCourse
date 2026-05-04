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
  xss|ssti|ssrf|authz|events|stored-comments|second-order-signature|markdown-preview|svg-preview|url-bookmarks|ssti-mail|ssti-theme|authz-orders|authz-notes|authz-tickets)
    CONTENT_DB_PATH="$ROOT/app/data/content.db" python3 app/reset_content.py "$TARGET"
    ;;
  *)
    echo "用法: ./scripts/reset_lab.sh [all|sqli|sqli-grades|sqli-filters|xss|ssti|ssrf|authz|events|stored-comments|second-order-signature|markdown-preview|svg-preview|url-bookmarks|ssti-mail|ssti-theme|authz-orders|authz-notes|authz-tickets]" >&2
    exit 1
    ;;
esac
