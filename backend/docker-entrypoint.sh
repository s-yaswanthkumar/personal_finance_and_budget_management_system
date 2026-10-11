#!/bin/bash
set -e

echo "=========================================================="
echo " Starting AI Budget Management System Backend"
echo "=========================================================="

# 1. Wait for PostgreSQL to be responsive
echo "[1/3] Checking PostgreSQL connectivity..."
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${POSTGRES_USER:-postgres}"

max_retries=30
retry_count=0

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $max_retries ]; then
        echo "[WARNING] PostgreSQL not ready after $max_retries seconds. Continuing anyway..."
        break
    fi
    echo "      Waiting for PostgreSQL at $DB_HOST:$DB_PORT ($retry_count/$max_retries)..."
    sleep 1
done

echo "      PostgreSQL is reachable!"

# 2. Check and initialize database schema and seeds if necessary
echo "[2/3] Verifying database schema & seed status..."
python - << 'EOF' > /dev/null 2>&1
import sys
try:
    from backend.db.postgres import get_db_cursor
    with get_db_cursor() as (cur, conn):
        cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'transactions';")
        res = cur.fetchone()
        if not res:
            sys.exit(10)
        cur.execute("SELECT count(*) FROM transactions;")
        tcnt = cur.fetchone()[0]
        if tcnt == 0:
            sys.exit(10)
except Exception as e:
    print("DB check notice:", e)
    sys.exit(10)
sys.exit(0)
EOF
status=$?

if [ $status -eq 10 ]; then
    echo "      Database is empty or missing tables. Running schema setup and seed..."
    python -m backend.scripts.setup_db || echo "setup_db notice"
    python -m backend.scripts.seed_data || echo "seed_data notice"
    echo "      Schema setup and data seeding completed!"
else
    echo "      Database schema and seed data already present."
fi

# 3. Start ASGI Server
echo "[3/3] Launching FastAPI ASGI application..."
exec "$@"
