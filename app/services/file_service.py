from __future__ import annotations

from app.config.settings import (
    CLIPS_DIR,
    DATABASE_DIR,
    EXPORTS_DIR,
    KEYFRAMES_DIR,
    LOGS_DIR,
    ORIGINALS_DIR,
    TEMP_DIR,
    THUMBNAILS_DIR,
)


def ensure_library_directories() -> None:
    for directory in [ORIGINALS_DIR, CLIPS_DIR, THUMBNAILS_DIR, KEYFRAMES_DIR, EXPORTS_DIR, DATABASE_DIR, LOGS_DIR, TEMP_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
