import os
import sqlite3
from pathlib import Path
from typing import Optional


DEFAULT_DB_PATH = Path("data/attendance.db")


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS attendance_logs (
    id INTEGER PRIMARY KEY,
    userid TEXT,
    username TEXT,
    department TEXT,
    datetime TIMESTAMP,
    status TEXT,
    device_id TEXT,
    verify_code INTEGER,
    imported_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sync_status (
    device_id TEXT PRIMARY KEY,
    last_sync TIMESTAMP,
    total_records INTEGER
);
"""


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_schema(conn: Optional[sqlite3.Connection] = None) -> None:
    owns_conn = False
    if conn is None:
        conn = get_connection()
        owns_conn = True
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        if owns_conn:
            conn.close()


def get_last_sync(conn: sqlite3.Connection, device_id: str = "ACCESS") -> Optional[str]:
    cur = conn.execute("SELECT last_sync FROM sync_status WHERE device_id = ?", (device_id,))
    row = cur.fetchone()
    return row[0] if row and row[0] else None


def update_last_sync(conn: sqlite3.Connection, last_sync: Optional[str], total_records: int, device_id: str = "ACCESS") -> None:
    conn.execute(
        "INSERT INTO sync_status(device_id, last_sync, total_records) VALUES(?,?,?) ON CONFLICT(device_id) DO UPDATE SET last_sync=excluded.last_sync, total_records=excluded.total_records",
        (device_id, last_sync, total_records),
    )
    conn.commit()

