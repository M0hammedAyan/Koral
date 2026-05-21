#!/usr/bin/env python3
"""Clear incidents from the KORAL database (safe helper).

Usage: python scripts/clear_incidents.py
"""
import os
import sqlite3
from datetime import datetime

# Determine DB type and path (defaults match backend.database)
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "koral.db"))


def _count_sqlite(path):
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM incidents")
        row = cur.fetchone()
        conn.close()
        return int(row[0]) if row else 0
    except Exception:
        return 0


def _clear_sqlite(path):
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("DELETE FROM incidents")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"SQLite clear error: {e}")
        return False


def clear():
    if DB_TYPE != "sqlite":
        print("DB_TYPE is not sqlite. To clear incidents for Postgres, run a maintenance job or use the backend admin endpoint.")
        return

    before = _count_sqlite(DB_PATH)
    print(f"Incidents before: {before}")
    ok = _clear_sqlite(DB_PATH)
    after = _count_sqlite(DB_PATH)
    if ok:
        print(f"Incidents after: {after}")
    else:
        print("Failed to clear incidents")


if __name__ == '__main__':
    clear()
