import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from backend.config import POSTGRES_URL

_pool = None

def init_pool(minconn=1, maxconn=10):
    global _pool
    if _pool is None or _pool.closed:
        _pool = pool.ThreadedConnectionPool(minconn, maxconn, POSTGRES_URL)
    return _pool

def get_pool():
    global _pool
    if _pool is None or _pool.closed:
        init_pool()
    return _pool

@contextmanager
def get_db_connection():
    p = get_pool()
    conn = p.getconn()
    try:
        yield conn
    finally:
        p.putconn(conn)

@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor, conn
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

def get_postgres_stats(user_id: int = None) -> dict:
    """Retrieve operational statistics and table counts from PostgreSQL."""
    stats = {
        "engine": "PostgreSQL 18.4",
        "connected": True,
        "tables": {},
        "pgvector": {}
    }
    try:
        with get_db_cursor() as (cur, conn):
            cur.execute("SELECT installed_version FROM pg_available_extensions WHERE name = 'vector';")
            ext = cur.fetchone()
            stats["pgvector"] = {
                "installed": ext is not None and ext[0] is not None,
                "version": ext[0] if ext else None,
                "dimension": 64
            }
            cur.execute("SELECT count(*) FROM transactions;")
            stats["tables"]["transactions"] = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM accounts;")
            stats["tables"]["accounts"] = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM budgets;")
            stats["tables"]["budgets"] = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM users;")
            stats["tables"]["users"] = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM transactions WHERE embedding IS NOT NULL;")
            stats["tables"]["embedded_transactions"] = cur.fetchone()[0]
            if user_id:
                cur.execute("SELECT count(*) FROM transactions WHERE user_id = %s;", (user_id,))
                stats["user_transaction_count"] = cur.fetchone()[0]
    except Exception as e:
        stats["connected"] = False
        stats["error"] = str(e)
    return stats
