#!/bin/bash
# Entrypoint script for UMS backend
# Waits for PostgreSQL to be ready before running migrations and starting the API

set -e

# Configuration
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-ums_user}
DB_NAME=${DB_NAME:-ums_db}
MAX_RETRIES=30
RETRY_INTERVAL=2

echo "[ENTRYPOINT] Starting UMS Backend..."
echo "[ENTRYPOINT] Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

# Function to check if PostgreSQL is ready
check_postgres_ready() {
    pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" 2>/dev/null
    return $?
}

# Wait for PostgreSQL to be ready
retry_count=0
while [ $retry_count -lt $MAX_RETRIES ]; do
    if check_postgres_ready; then
        echo "[ENTRYPOINT] ✓ PostgreSQL is ready!"
        break
    fi
    
    retry_count=$((retry_count + 1))
    echo "[ENTRYPOINT] PostgreSQL not ready yet... (attempt $retry_count/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done

# Check if we timed out
if [ $retry_count -eq $MAX_RETRIES ]; then
    echo "[ENTRYPOINT] ✗ FATAL: PostgreSQL did not become ready after $((MAX_RETRIES * RETRY_INTERVAL)) seconds"
    exit 1
fi

echo "[ENTRYPOINT] Running database migrations..."
alembic upgrade head

echo "[ENTRYPOINT] Seeding database (if needed)..."
python -m scripts.seed

echo "[ENTRYPOINT] Starting Uvicorn API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
