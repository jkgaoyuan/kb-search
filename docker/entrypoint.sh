#!/bin/sh
set -e

# Only run migrations for web service (gunicorn/uvicorn)
# Skip for celery workers/beat to avoid concurrent migration attempts
case "$1" in
    gunicorn*|uvicorn*)
        echo "Waiting for database..."
        for i in $(seq 1 30); do
            if python -c "import socket; socket.create_connection(('db', 5432), timeout=1)" 2>/dev/null; then
                echo "Database is ready"
                break
            fi
            if [ "$i" -eq 30 ]; then
                echo "Database connection timed out"
                exit 1
            fi
            sleep 1
        done

        echo "Running database migrations..."
        alembic upgrade head
        ;;
    *)
        echo "Skipping migrations for command: $1"
        ;;
esac

echo "Starting application..."
exec "$@"
