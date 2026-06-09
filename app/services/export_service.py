from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.config.settings import EXPORTS_DIR, FFMPEG_PATH
from app.db import queries
from app.db.database import get_connection
from app.utils.ffmpeg_utils import run_command


def export_extended_clip(clip_id: int, extend_before_seconds: float, extend_after_seconds: float, export_mode: str = "copy") -> str:
    with get_connection() as conn:
        clip = queries.get_clip_by_id(conn, clip_id)
        if not clip:
            raise ValueError(f"Clip not found: {clip_id}")

        source_video = queries.get_source_video_by_id(conn, clip["source_video_id"])
        if not source_video:
            raise ValueError(f"Source video not found: {clip['source_video_id']}")

        source_path = Path(source_video["file_path"])
        if not source_path.exists():
            raise FileNotFoundError(f"原视频丢失: {source_path}")

        source_id = clip["source_video_id"]
        duration = float(source_video["duration"] or 0.0)
        original_start = float(clip["source_start_time"] or 0.0)
        original_end = float(clip["source_end_time"] or original_start)

        before = float(extend_before_seconds)
        after = float(extend_after_seconds)
        if before < 0 or after < 0:
            raise ValueError("延展秒数不能小于 0")

        new_start = max(0.0, original_start - before)
        new_end = min(duration, original_end + after)
        if new_end <= new_start:
            raise ValueError("导出时间范围无效")

        export_dir = EXPORTS_DIR / f"source_{source_id:06d}"
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = (
            export_dir
            / f"clip_{clip_id:06d}_ext_{int(extend_before_seconds * 1000)}ms_"
              f"{int(extend_after_seconds * 1000)}ms_{uuid4().hex[:8]}.mp4"
        )

        if export_mode == "copy":
            codec_args = ["-c", "copy"]
            export_type = "copy"
        else:
            codec_args = ["-c:v", "libx264", "-c:a", "aac"]
            export_type = "encode"

        cmd = [
            FFMPEG_PATH,
            "-y",
            "-ss", str(round(new_start, 3)),
            "-to", str(round(new_end, 3)),
            "-i", str(source_path),
            *codec_args,
            str(export_path),
        ]
        run_command(cmd)
        if not export_path.exists():
            raise RuntimeError("导出失败，未生成文件")

        queries.insert_export_record(
            conn=conn,
            clip_id=clip_id,
            source_video_id=source_id,
            export_path=str(export_path),
            export_start_time=new_start,
            export_end_time=new_end,
            export_duration=round(new_end - new_start, 3),
            export_type=export_type,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        return str(export_path)
