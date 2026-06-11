from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

from app.config.settings import CLIPS_DIR, FFMPEG_PATH, MIN_CLIP_DURATION, TARGET_CLIP_DURATION
from app.db import queries
from app.db.database import get_connection
from app.utils.ffmpeg_utils import run_command
from app.utils.logger import configure_logging
from app.i18n import t

LOGGER = configure_logging()


def build_fixed_segments(duration: float, target_duration: float = TARGET_CLIP_DURATION) -> List[tuple[float, float]]:
    segments = []
    cursor = 0.0
    while cursor + MIN_CLIP_DURATION <= duration:
        end = min(cursor + target_duration, duration)
        if end - cursor < MIN_CLIP_DURATION:
            break
        segments.append((round(cursor, 3), round(end, 3)))
        cursor = end
    return segments


def split_video_fixed(source_video_id: int, target_duration: float = TARGET_CLIP_DURATION) -> list[int]:
    with get_connection() as conn:
        source_video = queries.get_source_video_by_id(conn, source_video_id)
        if not source_video:
            raise ValueError(f"Source video not found: {source_video_id}")

        source_path = Path(source_video["file_path"])
        duration = float(source_video["duration"] or 0.0)
        if not source_path.exists():
            raise FileNotFoundError(t("service_source_video_missing", source_path=source_path))

        segments = build_fixed_segments(duration, target_duration)
        created_ids: list[int] = []

        source_dir = CLIPS_DIR / f"source_{source_video_id:06d}"
        source_dir.mkdir(parents=True, exist_ok=True)

        existing = { (r["source_start_time"], r["source_end_time"]): r["id"] for r in queries.get_clips_by_source(conn, source_video_id)}
        failed_segments: list[str] = []
        queries.set_source_note(conn, source_video_id, None)

        for idx, (start_time, end_time) in enumerate(segments, start=1):
            if (start_time, end_time) in existing:
                continue
            clip_path = source_dir / f"clip_{idx:06d}.mp4"
            cmd = [
                FFMPEG_PATH,
                "-y",
                "-ss", str(start_time),
                "-to", str(end_time),
                "-i", str(source_path),
                "-c", "copy",
                str(clip_path),
            ]
            LOGGER.info("split clip: %s", cmd)
            try:
                run_command(cmd)
            except Exception as err:
                failed_segments.append(f"{start_time:.3f}-{end_time:.3f}: {err}")
                continue
            if not clip_path.exists():
                failed_segments.append(t("service_clip_output_missing", start_time=start_time, end_time=end_time))
                continue
            clip_duration = max(0.0, end_time - start_time)
            clip_id = queries.insert_clip(
                conn=conn,
                source_video_id=source_video_id,
                clip_path=str(clip_path),
                source_start_time=start_time,
                source_end_time=end_time,
                clip_duration=clip_duration,
                created_at=datetime.now().isoformat(timespec="seconds"),
            )
            created_ids.append(clip_id)

        if failed_segments:
            queries.append_source_note(
                conn,
                source_video_id,
                t("service_fixed_split_failed", details="; ".join(failed_segments)),
            )
        else:
            queries.append_source_note(conn, source_video_id, t("service_fixed_split_done"))

        queries.update_clip_neighbors(conn, source_video_id)
        return created_ids
