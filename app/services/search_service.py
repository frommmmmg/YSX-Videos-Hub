from __future__ import annotations

from app.db import queries
from app.db.database import get_connection


def search_clips(query: str | None, page: int = 1, page_size: int = 24):
    with get_connection() as conn:
        return queries.search_clips(conn, query, page=page, page_size=page_size)


def get_home_stats():
    with get_connection() as conn:
        return queries.get_home_stats(conn)
