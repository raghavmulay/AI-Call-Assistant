"""
queries.py — Reusable query execution helpers.

WHY THIS FILE EXISTS:
  Raw psycopg cursor handling is repetitive and error-prone.
  These helpers centralize:
    - connection lifecycle (open → execute → close)
    - parameterized queries (prevents SQL injection)
    - exception handling (no silent failures)
  Services call these helpers instead of writing raw DB code.
  This keeps service files clean and focused on business logic only.
"""

import psycopg.rows
from backend.database.database import get_connection


def execute_query(sql: str, params: tuple = ()) -> bool:
    """
    Executes INSERT / UPDATE / DELETE statements.
    Returns True on success, False on failure.
    Always uses parameterized queries — never string formatting.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()
        return True
    except Exception as e:
        print(f"[DB] execute_query error: {e}")
        return False


def fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    """
    Executes a SELECT and returns all matching rows as a list of dicts.
    Returns empty list if no rows found or on error.
    Dict keys = column names — easy to use directly in AI handlers.
    """
    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchall()
    except Exception as e:
        print(f"[DB] fetch_all error: {e}")
        return []


def fetch_one(sql: str, params: tuple = ()) -> dict | None:
    """
    Executes a SELECT and returns a single row as a dict.
    Returns None if no row found or on error.
    Used for lookups by unique key (PRN, ID, etc.).
    """
    try:
        with get_connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchone()
    except Exception as e:
        print(f"[DB] fetch_one error: {e}")
        return None
