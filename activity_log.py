"""Bounded local activity audit; no CSR/private-key/password contents."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone
from watch_store import data_dir

def db_path() -> Path: return data_dir()/'activity.db'

@contextmanager
def _connect(path: Path | None = None):
    # A sqlite3 connection context manager commits but does not close the handle.
    # Windows prevents deletion of the database until it is explicitly closed.
    conn = sqlite3.connect(str(path or db_path()), timeout=5)
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS activity (id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, operation TEXT NOT NULL, domain TEXT NOT NULL, output_path TEXT NOT NULL, result TEXT NOT NULL)')
        with conn:
            yield conn
    finally:
        conn.close()

def record(operation: str, domain: str, output_path: str, result: str='Success', path: Path | None = None):
    with _connect(path) as db:
        db.execute('INSERT INTO activity(timestamp,operation,domain,output_path,result) VALUES(?,?,?,?,?)',
                   (datetime.now(timezone.utc).isoformat(),str(operation)[:60],str(domain)[:253],str(output_path)[:2048],str(result)[:50]))
        db.execute('DELETE FROM activity WHERE id NOT IN (SELECT id FROM activity ORDER BY id DESC LIMIT 5000)')

def recent(limit: int = 300, path: Path | None = None):
    with _connect(path) as db:
        return db.execute('SELECT timestamp,operation,domain,output_path,result FROM activity ORDER BY id DESC LIMIT ?', (min(max(limit,1),1000),)).fetchall()

def clear(path: Path | None = None):
    with _connect(path) as db: db.execute('DELETE FROM activity')
