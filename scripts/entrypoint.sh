#!/usr/bin/env bash
set -euo pipefail

run_migrations() {
    echo "Running database migrations..."
    if ! /app/.venv/bin/alembic upgrade head; then
        echo "Migration failed!"
        return 1
    fi
    echo "Migrations completed successfully."
}

if [[ "${RUN_MIGRATIONS:-false}" == "true" ]]; then
    if ! run_migrations; then
        echo "Exiting due to migration failure"
        exit 1
    fi
fi

exec "$@"
