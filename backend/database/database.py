"""
database.py — PostgreSQL connection utility.

WHY THIS FILE EXISTS:
  All DB connection logic lives in one place.
  Every other file imports get_connection() from here.
  If credentials change, you update only this file.
  Future FastAPI integration just imports this same utility.
"""

import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

# ── Connection config ──────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",   "localhost"),
    "port":     os.getenv("DB_PORT",   "5432"),
    "dbname":   os.getenv("DB_NAME",   "ai_assistant_db"),
    "user":     os.getenv("DB_USER",   "postgres"),
    "password": os.getenv("DB_PASS",   ""),
}


def get_connection() -> psycopg.Connection:
    """
    Opens and returns a new PostgreSQL connection.
    Caller is responsible for closing it (use with `with` block).
    """
    return psycopg.connect(**DB_CONFIG)


def test_connection() -> bool:
    """
    Verifies the database is reachable.
    Prints status. Returns True if successful, False otherwise.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        print("[DB] Connection successful.")
        return True
    except Exception as e:
        print(f"[DB] Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
