from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any

from app.config.settings import MAX_PAGE_SIZE
from app.db import queries
from app.db.database import get_connection, init_database
from app.services.export_service import export_extended_clip
from app.services.file_service import ensure_library_directories
from app.services.keyframe_extractor import extract_keyframes
from app.services.tagger import tag_clip
from app.services.video_importer import import_video
from app.services.video_splitter import split_video_fixed


def _ensure_runtime_ready() -> None:
    ensure_library_directories()
    init_database()


def _as_json(payload: dict[str, Any], pretty: bool = False) -> str:
    if pretty:
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return json.dumps(payload, ensure_ascii=False)


def _success(command: str, data: Any = None, message: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": True,
        "command": command,
    }
    if message is not None:
        result["message"] = message
    if data is not None:
        result["data"] = data
    return result


def _fail(command: str, error: str, details: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "command": command,
        "error": error,
    }
    if details is not None:
        result["details"] = details
    return result


def _parse_json_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="app.cli",
        description="Video Material Library automation CLI",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--debug", action="store_true", help="Print traceback on failure.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    cmd_import = subparsers.add_parser("import", help="Import one video into library.")
    cmd_import.add_argument("video", help="Path to source video.")
    cmd_import.set_defaults(func=cmd_import)

    cmd_process = subparsers.add_parser(
        "process",
        help="Import video, split fixed clips, then extract keyframes.",
    )
    cmd_process.add_argument("video", help="Path to source video.")
    cmd_process.add_argument(
        "--target-duration",
        type=float,
        default=4.0,
        help="Fixed clip length in seconds.",
    )
    cmd_process.add_argument(
        "--tag",
        action="store_true",
        help="Run AI tagging after keyframes are extracted.",
    )
    cmd_process.set_defaults(func=cmd_process)

    cmd_split = subparsers.add_parser(
        "split",
        help="Split existing source video into fixed clips.",
    )
    cmd_split.add_argument("source_video_id", type=int)
    cmd_split.add_argument(
        "--target-duration",
        type=float,
        default=4.0,
        help="Fixed clip length in seconds.",
    )
    cmd_split.set_defaults(func=cmd_split)

    cmd_keyframes = subparsers.add_parser(
        "keyframes",
        help="Extract keyframes for one clip.",
    )
    cmd_keyframes.add_argument("clip_id", type=int)
    cmd_keyframes.set_defaults(func=cmd_keyframes)

    cmd_tag = subparsers.add_parser("tag", help="Generate tags for one clip.")
    cmd_tag.add_argument("clip_id", type=int)
    cmd_tag.set_defaults(func=cmd_tag)

    cmd_export = subparsers.add_parser("export", help="Export clip with optional extensions.")
    cmd_export.add_argument("clip_id", type=int)
    cmd_export.add_argument("--before", type=float, default=0.0, help="Seconds before the clip start.")
    cmd_export.add_argument("--after", type=float, default=0.0, help="Seconds after the clip end.")
    cmd_export.add_argument(
        "--mode",
        choices=["copy", "encode"],
        default="copy",
        help="Export mode.",
    )
    cmd_export.set_defaults(func=cmd_export)

    cmd_search = subparsers.add_parser("search", help="Search clips in local library.")
    cmd_search.add_argument("query", help="Text to match in file name, description, or tags.")
    cmd_search.add_argument("--page", type=int, default=1)
    cmd_search.add_argument("--page-size", type=int, default=24)
    cmd_search.set_defaults(func=cmd_search)

    cmd_stats = subparsers.add_parser("stats", help="Print quick library statistics.")
    cmd_stats.set_defaults(func=cmd_stats)

    cmd_sources = subparsers.add_parser("sources", help="List imported source videos.")
    cmd_sources.add_argument("--limit", type=int, default=200)
    cmd_sources.add_argument("--offset", type=int, default=0)
    cmd_sources.set_defaults(func=cmd_sources)

    cmd_clip = subparsers.add_parser("clip", help="Get one clip detail.")
    cmd_clip.add_argument("clip_id", type=int)
    cmd_clip.set_defaults(func=cmd_clip)

    return parser.parse_args()


def cmd_import(args: argparse.Namespace) -> dict[str, Any]:
    source_video_id, is_new = import_video(args.video)
    return _success(
        "import",
        {
            "source_video_id": source_video_id,
            "is_new": is_new,
        },
        "Video imported.",
    )


def cmd_process(args: argparse.Namespace) -> dict[str, Any]:
    source_video_id, is_new = import_video(args.video)
    clip_ids = split_video_fixed(source_video_id, target_duration=args.target_duration)
    keyframes: dict[int, int] = {}
    tagged: dict[int, dict[str, Any]] = {}

    for clip_id in clip_ids:
        frames = extract_keyframes(clip_id)
        keyframes[clip_id] = len(frames)
        if args.tag:
            tagged[clip_id] = tag_clip(clip_id)

    result: dict[str, Any] = {
        "source_video_id": source_video_id,
        "is_new": is_new,
        "clip_ids": clip_ids,
        "keyframe_count": keyframes,
    }
    if args.tag:
        result["tags"] = tagged
    return _success("process", result, "Video processed.")


def cmd_split(args: argparse.Namespace) -> dict[str, Any]:
    clip_ids = split_video_fixed(args.source_video_id, target_duration=args.target_duration)
    return _success(
        "split",
        {
            "source_video_id": args.source_video_id,
            "clip_ids": clip_ids,
            "created_count": len(clip_ids),
        },
    )


def cmd_keyframes(args: argparse.Namespace) -> dict[str, Any]:
    frames = extract_keyframes(args.clip_id)
    frame_paths = [frame["frame_path"] for frame in frames if "frame_path" in frame]
    return _success(
        "keyframes",
        {
            "clip_id": args.clip_id,
            "frame_count": len(frames),
            "frame_paths": frame_paths,
        },
        "Keyframes extracted.",
    )


def cmd_tag(args: argparse.Namespace) -> dict[str, Any]:
    tags = tag_clip(args.clip_id)
    return _success(
        "tag",
        {
            "clip_id": args.clip_id,
            "tags": tags,
        },
        "Clip tagged.",
    )


def cmd_export(args: argparse.Namespace) -> dict[str, Any]:
    export_path = export_extended_clip(args.clip_id, args.before, args.after, args.mode)
    return _success(
        "export",
        {
            "clip_id": args.clip_id,
            "export_path": export_path,
        },
        "Export completed.",
    )


def cmd_search(args: argparse.Namespace) -> dict[str, Any]:
    page_size = max(1, min(args.page_size, MAX_PAGE_SIZE))
    with get_connection() as conn:
        rows, total = queries.search_clips(conn, args.query, page=args.page, page_size=page_size)
    return _success(
        "search",
        {
            "query": args.query,
            "page": args.page,
            "page_size": page_size,
            "total": total,
            "items": rows,
        },
    )


def cmd_stats(_: argparse.Namespace) -> dict[str, Any]:
    with get_connection() as conn:
        stats = queries.get_home_stats(conn)
    return _success("stats", {"stats": stats})


def cmd_sources(args: argparse.Namespace) -> dict[str, Any]:
    with get_connection() as conn:
        rows = queries.get_source_videos(conn, limit=args.limit, offset=args.offset)
    return _success(
        "sources",
        {
            "limit": args.limit,
            "offset": args.offset,
            "items": rows,
        },
    )


def cmd_clip(args: argparse.Namespace) -> dict[str, Any]:
    with get_connection() as conn:
        clip = queries.get_clip_by_id(conn, args.clip_id)
        if not clip:
            raise ValueError(f"Clip not found: {args.clip_id}")
        keyframes = queries.get_clip_keyframes(conn, args.clip_id)
        tags = queries.get_clip_tags(conn, args.clip_id)
    return _success(
        "clip",
        {
            "clip": clip,
            "keyframes": keyframes,
            "tags": tags,
        },
        "Clip detail loaded.",
    )


def main() -> None:
    args = _parse_json_args()
    _ensure_runtime_ready()
    try:
        result = args.func(args)
        if not isinstance(result, dict):
            result = {"ok": False, "error": "Invalid command result", "command": args.command}
        print(_as_json(result, pretty=args.pretty))
    except Exception as exc:
        details = None
        if args.debug:
            details = traceback.format_exc()
        print(_as_json(_fail(args.command, str(exc), details=details)), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

