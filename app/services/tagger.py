from __future__ import annotations

from datetime import datetime

from app.config.settings import TAGGER_BACKEND
from app.db import queries
from app.db.database import get_connection


class BaseTagger:
    def tag_clip(self, keyframe_paths: list[str]) -> dict:
        raise NotImplementedError


class MockTagger(BaseTagger):
    def tag_clip(self, keyframe_paths: list[str]) -> dict:
        return {
            "theme": ["测试素材"],
            "objects": ["未知物体"],
            "scene": ["未知场景"],
            "action": ["未知动作"],
            "shot": ["未知镜头"],
            "style": ["真实拍摄"],
            "color": ["自然色"],
            "lighting": ["自然光"],
            "mood": ["普通"],
            "use_case": ["备用素材"],
            "description": "这是一段待识别的视频素材。",
        }


class ReservedTagger(BaseTagger):
    """
    预留接口：后续可替换为在线或本地模型实现。
    先保留签名和返回结构，不在此版本做真实调用。
    """

    def __init__(self, source: str):
        self.source = source

    def tag_clip(self, keyframe_paths: list[str]) -> dict:
        raise NotImplementedError(
            f"AI识别已预留但未接入（source={self.source}）。请配置并实现对应实现类。"
        )


def get_tagger() -> BaseTagger:
    if TAGGER_BACKEND == "mock":
        return MockTagger()
    return ReservedTagger(TAGGER_BACKEND)


def tag_clip(clip_id: int) -> dict:
    with get_connection() as conn:
        keyframes = queries.get_clip_keyframes(conn, clip_id)
        if not keyframes:
            raise ValueError(f"该 clip 没有可用于识别的关键帧: {clip_id}")

        tagger = get_tagger()
        keyframe_paths = [k["frame_path"] for k in keyframes]

        tags = tagger.tag_clip(keyframe_paths)
        queries.clear_clip_tags(conn, clip_id)

        for field in [
            "theme", "objects", "scene", "action", "shot", "style", "color",
            "lighting", "mood", "use_case",
        ]:
            values = tags.get(field, [])
            for value in values:
                if isinstance(value, str):
                    queries.insert_clip_tag(conn, clip_id=clip_id, tag_type=field, tag_value=value, confidence=1.0)

        description = tags.get("description") or "未识别"
        queries.set_clip_description(conn, clip_id=clip_id, description=description)
        return tags
