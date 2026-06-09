from __future__ import annotations

import re


def _row_to_dict(row):
    return dict(row) if row is not None else None


def get_source_video_by_hash(conn, file_hash: str):
    cur = conn.execute(
        "SELECT * FROM source_videos WHERE file_hash = ? AND status = 'active' LIMIT 1;",
        (file_hash,),
    )
    return _row_to_dict(cur.fetchone())


def get_source_video_by_id(conn, source_video_id: int):
    cur = conn.execute(
        "SELECT * FROM source_videos WHERE id = ? LIMIT 1;",
        (source_video_id,),
    )
    return _row_to_dict(cur.fetchone())


def get_source_videos(conn, limit: int = 200, offset: int = 0):
    cur = conn.execute(
        "SELECT * FROM source_videos ORDER BY imported_at DESC LIMIT ? OFFSET ?;",
        (limit, offset),
    )
    return [_row_to_dict(r) for r in cur.fetchall()]


def insert_source_video(conn, payload: dict) -> int:
    cursor = conn.execute(
        """
        INSERT INTO source_videos (
            file_path, file_name, file_hash, file_size, duration,
            width, height, resolution, fps, codec, bitrate, orientation,
            has_audio, imported_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active');
        """,
        (
            payload["file_path"],
            payload["file_name"],
            payload["file_hash"],
            payload.get("file_size"),
            payload.get("duration"),
            payload.get("width"),
            payload.get("height"),
            payload.get("resolution"),
            payload.get("fps"),
            payload.get("codec"),
            payload.get("bitrate"),
            payload.get("orientation"),
            payload.get("has_audio", 0),
            payload["imported_at"],
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_clip_by_id(conn, clip_id: int):
    cur = conn.execute(
        """
        SELECT
            c.*,
            s.file_name AS source_file_name,
            s.file_path AS source_file_path,
            s.duration AS source_duration
        FROM clips c
        JOIN source_videos s ON s.id = c.source_video_id
        WHERE c.id = ?
        """,
        (clip_id,),
    )
    return _row_to_dict(cur.fetchone())


def get_clips_by_source(conn, source_video_id: int):
    cur = conn.execute(
        """
        SELECT * FROM clips
        WHERE source_video_id = ?
        ORDER BY source_start_time ASC;
        """,
        (source_video_id,),
    )
    return [_row_to_dict(r) for r in cur.fetchall()]


def insert_clip(
    conn,
    source_video_id: int,
    clip_path: str,
    source_start_time: float,
    source_end_time: float,
    clip_duration: float,
    created_at: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO clips (
            source_video_id, clip_path, source_start_time, source_end_time,
            clip_duration, created_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, 'active');
        """,
        (
            source_video_id,
            clip_path,
            source_start_time,
            source_end_time,
            clip_duration,
            created_at,
        ),
    )
    conn.commit()
    return cur.lastrowid


def update_clip_neighbors(conn, source_video_id: int) -> None:
    rows = get_clips_by_source(conn, source_video_id)
    rows.sort(key=lambda r: r["source_start_time"])

    for idx, row in enumerate(rows):
        prev_id = rows[idx - 1]["id"] if idx > 0 else None
        next_id = rows[idx + 1]["id"] if idx + 1 < len(rows) else None

        conn.execute(
            "UPDATE clips SET prev_clip_id = ?, next_clip_id = ? WHERE id = ?;",
            (prev_id, next_id, row["id"]),
        )
    conn.commit()


def set_clip_thumbnail(conn, clip_id: int, thumbnail_path: str | None) -> None:
    conn.execute(
        "UPDATE clips SET thumbnail_path = ? WHERE id = ?;",
        (thumbnail_path, clip_id),
    )
    conn.commit()


def set_clip_description(conn, clip_id: int, description: str) -> None:
    conn.execute(
        "UPDATE clips SET description = ? WHERE id = ?;",
        (description, clip_id),
    )
    conn.commit()


def set_clip_note(conn, clip_id: int, note: str | None) -> None:
    conn.execute(
        "UPDATE clips SET note = ? WHERE id = ?;",
        (note, clip_id),
    )
    conn.commit()


def append_source_note(conn, source_video_id: int, note: str) -> None:
    source = conn.execute(
        "SELECT COALESCE(note, '') AS note FROM source_videos WHERE id = ?",
        (source_video_id,),
    ).fetchone()
    old_note = source["note"] if source is not None else ""
    new_note = str(note)
    if old_note and new_note not in old_note:
        new_note = f"{old_note}\n{note}"
    conn.execute(
        "UPDATE source_videos SET note = ? WHERE id = ?;",
        (new_note, source_video_id),
    )
    conn.commit()


def set_source_note(conn, source_video_id: int, note: str | None) -> None:
    conn.execute(
        "UPDATE source_videos SET note = ? WHERE id = ?;",
        (note, source_video_id),
    )
    conn.commit()


def insert_clip_keyframe(
    conn,
    clip_id: int,
    frame_order: int,
    frame_role: str,
    frame_time_in_clip: float,
    frame_time_in_source: float,
    frame_path: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO clip_keyframes (
            clip_id, frame_order, frame_role, frame_time_in_clip,
            frame_time_in_source, frame_path
        ) VALUES (?, ?, ?, ?, ?, ?);
        """,
        (
            clip_id,
            frame_order,
            frame_role,
            frame_time_in_clip,
            frame_time_in_source,
            frame_path,
        ),
    )
    conn.commit()
    return cur.lastrowid


def clear_clip_keyframes(conn, clip_id: int) -> None:
    conn.execute("DELETE FROM clip_keyframes WHERE clip_id = ?;", (clip_id,))
    conn.commit()


def get_clip_keyframes(conn, clip_id: int):
    cur = conn.execute(
        """
        SELECT * FROM clip_keyframes
        WHERE clip_id = ?
        ORDER BY frame_order ASC;
        """,
        (clip_id,),
    )
    return [_row_to_dict(r) for r in cur.fetchall()]


def insert_clip_tag(conn, clip_id: int, tag_type: str, tag_value: str, confidence: float = 1.0) -> int:
    cur = conn.execute(
        """
        INSERT INTO clip_tags (clip_id, tag_type, tag_value, confidence)
        VALUES (?, ?, ?, ?)
        """,
        (clip_id, tag_type, tag_value, confidence),
    )
    conn.commit()
    return cur.lastrowid


def clear_clip_tags(conn, clip_id: int) -> None:
    conn.execute("DELETE FROM clip_tags WHERE clip_id = ?;", (clip_id,))
    conn.commit()


def get_clip_tags(conn, clip_id: int):
    cur = conn.execute(
        """
        SELECT * FROM clip_tags
        WHERE clip_id = ?
        ORDER BY id ASC;
        """,
        (clip_id,),
    )
    return [_row_to_dict(r) for r in cur.fetchall()]


def insert_export_record(
    conn,
    clip_id: int,
    source_video_id: int,
    export_path: str,
    export_start_time: float,
    export_end_time: float,
    export_duration: float,
    export_type: str,
    created_at: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO clip_exports (
            clip_id, source_video_id, export_path, export_start_time,
            export_end_time, export_duration, export_type, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            clip_id,
            source_video_id,
            export_path,
            export_start_time,
            export_end_time,
            export_duration,
            export_type,
            created_at,
        ),
    )
    conn.commit()
    return cur.lastrowid


def search_clips(conn, query: str | None, page: int = 1, page_size: int = 24):
    page = max(page, 1)
    limit = min(max(page_size, 1), 120)
    offset = (page - 1) * limit

    where_sql = "WHERE c.status = 'active'"
    params: list = []

    if query:
        tokens = [t.strip().lower() for t in re.split(r"\s+", query.strip()) if t.strip()]
        if tokens:
            token_clauses = []
            for token in tokens:
                like = f"%{token}%"
                token_clauses.append(
                    "("
                    "lower(COALESCE(c.description, '')) LIKE ? OR "
                    "lower(COALESCE(s.file_name, '')) LIKE ? OR "
                    "lower(COALESCE(ct.tag_value, '')) LIKE ?"
                    ")"
                )
                params.extend([like, like, like])
            where_sql += " AND " + " AND ".join(token_clauses)

    base_from = """
        FROM clips c
        JOIN source_videos s ON s.id = c.source_video_id
        LEFT JOIN clip_tags ct ON ct.clip_id = c.id
    """

    total_sql = f"SELECT COUNT(DISTINCT c.id) as total {base_from} {where_sql};"
    total_row = _row_to_dict(conn.execute(total_sql, params).fetchone())
    total = total_row["total"] if total_row else 0

    data_sql = f"""
        SELECT DISTINCT
            c.id,
            c.source_video_id,
            c.clip_path,
            c.thumbnail_path,
            c.source_start_time,
            c.source_end_time,
            c.clip_duration,
            c.description,
            c.favorite,
            c.created_at,
            s.file_name AS source_file_name
        {base_from}
        {where_sql}
        ORDER BY c.created_at DESC
        LIMIT ? OFFSET ?;
    """
    rows = [_row_to_dict(r) for r in conn.execute(data_sql, params + [limit, offset]).fetchall()]
    return rows, total


def get_home_stats(conn):
    data = {}
    data["source_count"] = conn.execute(
        "SELECT COUNT(*) AS total FROM source_videos WHERE status = 'active';"
    ).fetchone()["total"]
    data["clip_count"] = conn.execute(
        "SELECT COUNT(*) AS total FROM clips WHERE status = 'active';"
    ).fetchone()["total"]
    data["keyframe_count"] = conn.execute(
        "SELECT COUNT(*) AS total FROM clip_keyframes;"
    ).fetchone()["total"]
    data["tag_count"] = conn.execute(
        "SELECT COUNT(*) AS total FROM clip_tags;"
    ).fetchone()["total"]
    data["favorite_count"] = conn.execute(
        "SELECT COUNT(*) AS total FROM clips WHERE favorite = 1;"
    ).fetchone()["total"]
    return data


def set_clip_favorite(conn, clip_id: int, favorite: bool) -> None:
    conn.execute("UPDATE clips SET favorite = ? WHERE id = ?;", (1 if favorite else 0, clip_id))
    conn.commit()
