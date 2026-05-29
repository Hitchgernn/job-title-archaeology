#!/bin/sh
set -e

if [ -n "$DATABASE_URL" ]; then
    DB_PATH=$(echo "$DATABASE_URL" | sed -e 's|^sqlite:///||')
    DB_DIR=$(dirname "$DB_PATH")
    mkdir -p "$DB_DIR"
    if [ ! -f "$DB_PATH" ] && [ -f /app/data/seed/job_title_archaeology.db ]; then
        echo "seeding $DB_PATH from /app/data/seed/job_title_archaeology.db"
        cp /app/data/seed/job_title_archaeology.db "$DB_PATH"
    fi
fi

exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
