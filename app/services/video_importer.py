from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from app.config.settings import ORIGINALS_DIR
from app.db import queries
from app.db.database import get_connection
from app.services.video_probe import probe_video
from app.utils.hash_utils import calculate_file_hash
from app.i18n import t


def import_video(video_path: str):
    source_path = Path(video_path).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(t("service_file_not_found", path=source_path))

    file_hash = calculate_file_hash(str(source_path))

    with get_connection() as conn:
        existed = queries.get_source_video_by_hash(conn, file_hash)
        if existed:
            return existed["id"], False

        meta = probe_video(str(source_path))
        safe_name = f"{file_hash[:12]}_{source_path.name}"
        target_path = ORIGINALS_DIR / safe_name
        if not target_path.exists():
            shutil.copy2(str(source_path), str(target_path))

        payload = {
            "file_path": str(target_path),
            "file_name": source_path.name,
            "file_hash": file_hash,
            "file_size": meta.get("file_size"),
            "duration": meta.get("duration"),
            "width": meta.get("width"),
            "height": meta.get("height"),
            "resolution": meta.get("resolution"),
            "fps": meta.get("fps"),
            "codec": meta.get("codec"),
            "bitrate": meta.get("bitrate"),
            "orientation": meta.get("orientation"),
            "has_audio": 1 if meta.get("has_audio") else 0,
            "imported_at": datetime.now().isoformat(timespec="seconds"),
        }
        source_video_id = queries.insert_source_video(conn, payload)
        return source_video_id, True
