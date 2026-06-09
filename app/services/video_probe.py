from __future__ import annotations

import json
from pathlib import Path

from app.config.settings import FFPROBE_PATH
from app.utils.ffmpeg_utils import run_command


def _parse_fps(value: str | None) -> float | None:
    if not value:
        return None
    if "/" in value:
        num, den = value.split("/", 1)
        try:
            return float(num) / float(den)
        except ZeroDivisionError:
            return None
    try:
        return float(value)
    except ValueError:
        return None


def probe_video(video_path: str) -> dict:
    cmd = [
        FFPROBE_PATH,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    proc = run_command(cmd)
    payload = json.loads(proc.stdout or "{}")

    streams = payload.get("streams", [])
    format_info = payload.get("format", {})

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video_stream is None:
        raise ValueError(f"No video stream found: {video_path}")

    width = int(video_stream.get("width", 0)) or None
    height = int(video_stream.get("height", 0)) or None
    codec = video_stream.get("codec_name")
    bitrate = video_stream.get("bit_rate") or format_info.get("bit_rate")
    bitrate = int(float(bitrate)) if bitrate else None
    fps = _parse_fps(video_stream.get("avg_frame_rate")) or _parse_fps(video_stream.get("r_frame_rate"))

    return {
        "duration": float(format_info.get("duration", 0.0) or 0.0),
        "width": width,
        "height": height,
        "fps": fps,
        "codec": codec,
        "bitrate": bitrate,
        "file_size": int(format_info.get("size", 0) or 0),
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
        "resolution": f"{width}x{height}" if width and height else None,
        "orientation": "landscape" if (width and height and width >= height) else "portrait" if width and height else None,
    }
