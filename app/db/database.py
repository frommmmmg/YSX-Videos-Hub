from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config.settings import DB_PATH


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _ensure_legacy_columns(conn: sqlite3.Connection) -> None:
    clip_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(clips)").fetchall()
    }
    if "note" not in clip_columns:
        conn.execute("ALTER TABLE clips ADD COLUMN note TEXT;")

    source_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(source_videos)").fetchall()
    }
    if "note" not in source_columns:
        conn.execute("ALTER TABLE source_videos ADD COLUMN note TEXT;")


def init_database() -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")

    with get_connection() as conn:
        conn.executescript(sql)
        _ensure_legacy_columns(conn)
        conn.commit()
