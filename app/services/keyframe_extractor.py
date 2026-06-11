from __future__ import annotations

import shutil
from pathlib import Path

from app.config.settings import FFMPEG_PATH, KEYFRAMES_DIR, THUMBNAILS_DIR
from app.db import queries
from app.db.database import get_connection
from app.utils.ffmpeg_utils import run_command
from app.utils.logger import configure_logging
from app.i18n import t

LOGGER = configure_logging()


def _calc_keyframe_count(duration: float) -> int:
    if duration < 3.0:
        return 3
    if duration < 5.0:
        return 4
    if duration < 8.0:
        return 5
    return 5


def _calc_frame_time_points(duration: float, count: int):
    if count <= 3:
        return [0.0, duration * 0.5, duration]
    if count == 4:
        return [duration * 0.10, duration * 0.35, duration * 0.65, duration * 0.90]
    return [duration * p for p in (0.05, 0.30, 0.50, 0.70, 0.95)]


def extract_keyframes(clip_id: int) -> list[dict]:
    with get_connection() as conn:
        clip = queries.get_clip_by_id(conn, clip_id)
        if not clip:
            raise ValueError(t("service_clip_not_found", clip_id=clip_id))

        clip_path = Path(clip["clip_path"])
        if not clip_path.exists():
            raise FileNotFoundError(t("service_clip_file_missing", path=clip_path))

        source_video_id = clip["source_video_id"]
        source_dir = KEYFRAMES_DIR / f"source_{source_video_id:06d}" / f"clip_{clip_id:06d}"
        source_dir.mkdir(parents=True, exist_ok=True)

        queries.clear_clip_keyframes(conn, clip_id)
        duration = float(clip["clip_duration"] or 0.0)
        count = _calc_keyframe_count(duration)
        times = _calc_frame_time_points(duration, count)
        clip_times = [(min(max(t, 0.0), max(duration - 0.001, 0.001)), idx + 1) for idx, t in enumerate(times)]

        frame_roles = []
        if count == 3:
            frame_roles = ["start", "mid", "end"]
        elif count == 4:
            frame_roles = ["start", "mid1", "mid2", "end"]
        else:
            frame_roles = ["start", "mid1", "center", "mid2", "end"]

        outputs: list[dict] = []
        for (seconds, idx), role in zip(clip_times, frame_roles):
            frame_path = source_dir / f"{idx:02d}_{role}.jpg"
            cmd = [
                FFMPEG_PATH,
                "-y",
                "-ss", f"{seconds:.3f}",
                "-i", str(clip_path),
                "-frames:v", "1",
                str(frame_path),
            ]
            LOGGER.info("extract keyframe: clip=%s idx=%s", clip_id, idx)
            try:
                run_command(cmd)
            except Exception as err:
                LOGGER.warning("extract keyframe failed: clip=%s idx=%s reason=%s", clip_id, idx, err)
                continue
            if not frame_path.exists():
                continue

            frame_time_in_source = float(clip["source_start_time"] or 0.0) + seconds
            keyframe_id = queries.insert_clip_keyframe(
                conn=conn,
                clip_id=clip_id,
                frame_order=idx,
                frame_role=role,
                frame_time_in_clip=seconds,
                frame_time_in_source=frame_time_in_source,
                frame_path=str(frame_path),
            )
            outputs.append({
                "id": keyframe_id,
                "frame_path": str(frame_path),
                "frame_order": idx,
                "frame_role": role,
            })

        thumb_src = next((o for o in outputs if o["frame_role"] == "mid1"), None)
        if thumb_src is None and outputs:
            thumb_src = outputs[1] if len(outputs) > 1 else outputs[0]

        if thumb_src:
            thumb_dir = THUMBNAILS_DIR / f"source_{source_video_id:06d}"
            thumb_dir.mkdir(parents=True, exist_ok=True)
            thumb_path = thumb_dir / f"clip_{clip_id:06d}.jpg"
            shutil.copyfile(thumb_src["frame_path"], str(thumb_path))
            queries.set_clip_thumbnail(conn, clip_id, str(thumb_path))
            queries.set_clip_note(conn, clip_id, None)
        else:
            queries.set_clip_note(conn, clip_id, t("service_keyframe_extract_no_frame"))

        return outputs
