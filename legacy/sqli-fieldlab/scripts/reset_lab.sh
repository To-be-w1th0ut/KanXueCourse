#!/usr/bin/env bash
set -euo pipefail

LAB_NAME="${1:-all}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_CMD=(docker compose)

cd "$PROJECT_ROOT"

run_sql_file() {
  local file="$1"
  "${COMPOSE_CMD[@]}" exec -T db mariadb -uroot -p"${MYSQL_ROOT_PASSWORD:-labroot}" sql_training < "$file"
}

case "$LAB_NAME" in
  all)
    "${COMPOSE_CMD[@]}" down -v
    "${COMPOSE_CMD[@]}" up -d --build
    ;;
  grade-editor)
    run_sql_file "$PROJECT_ROOT/db/resets/reset_grades.sql"
    ;;
  report-stacked)
    run_sql_file "$PROJECT_ROOT/db/resets/reset_grades.sql"
    ;;
  second-order)
    run_sql_file "$PROJECT_ROOT/db/resets/reset_saved_filters.sql"
    ;;
  *)
    echo "用法: ./scripts/reset_lab.sh [all|grade-editor|report-stacked|second-order]" >&2
    exit 1
    ;;
esac
