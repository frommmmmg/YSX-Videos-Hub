from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from app.config.settings import (
    TAGGER_BACKEND,
    TAGGER_MAX_KEYFRAMES,
    TAGGER_TIMEOUT_SECONDS,
    OLLAMA_API_BASE,
    OLLAMA_MODEL,
    STEPFUN_API_BASE,
    STEPFUN_API_KEY,
    STEPFUN_MODEL,
)
from app.db import queries
from app.db.database import get_connection
from app.i18n import t


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


class _TagPrompt:
    SYSTEM = (
        "你是短视频/视频素材分析助手。请基于多帧关键帧图像输出以下 JSON："
        "{"
        "\"theme\": [主题列表],"
        "\"objects\": [可见物体列表],"
        "\"scene\": [场景列表],"
        "\"action\": [动作列表],"
        "\"shot\": [镜头类型列表],"
        "\"style\": [风格列表],"
        "\"color\": [色彩风格列表],"
        "\"lighting\": [光线类型列表],"
        "\"mood\": [情绪/氛围列表],"
        "\"use_case\": [使用场景列表],"
        "\"description\": \"中文一句话描述\""
        "}"
        "仅返回 JSON，不要额外说明。"
    )
    TAG_FIELDS = [
        "theme", "objects", "scene", "action", "shot", "style",
        "color", "lighting", "mood", "use_case", "description",
    ]


def _read_image_as_base64(path: str) -> str:
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("utf-8")


def _detect_mime_type(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"


def _extract_json(response_text: str) -> dict[str, object]:
    payload = response_text.strip()
    if not payload:
        return {}

    fenced_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", payload, re.IGNORECASE)
    candidate = payload
    if fenced_match:
        candidate = fenced_match.group(1)

    if not candidate.startswith("{"):
        brace_match = re.search(r"\{[\s\S]*\}", candidate)
        if brace_match:
            candidate = brace_match.group(0)

    try:
        value = json.loads(candidate)
    except Exception:
        return {}

    return value if isinstance(value, dict) else {}


def _normalize_tags(payload: dict[str, object] | str) -> dict[str, object]:
    raw = payload
    if isinstance(payload, str):
        raw = _extract_json(payload)
    if not isinstance(raw, dict):
        return {"description": str(payload).strip()}

    result: dict[str, object] = {}
    for field in _TagPrompt.TAG_FIELDS:
        value = raw.get(field)
        if field == "description":
            if not isinstance(value, str):
                value = ""
            result[field] = value.strip()
            continue

        if isinstance(value, str):
            result[field] = [value.strip()] if value.strip() else []
            continue

        if isinstance(value, list):
            result[field] = [str(v).strip() for v in value if str(v).strip()]
            continue

        result[field] = []

    if "description" not in result:
        result["description"] = ""
    return result


def _post_json(url: str, payload: dict, timeout: int = 30) -> dict:
    request = urllib.request.Request(
        url,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response_text = response.read().decode("utf-8")
    return json.loads(response_text)


class OllamaVisionTagger(BaseTagger):
    def __init__(self, base_url: str = OLLAMA_API_BASE, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model or "llava:7b"

    def tag_clip(self, keyframe_paths: list[str]) -> dict:
        images = [_read_image_as_base64(p) for p in keyframe_paths[:TAGGER_MAX_KEYFRAMES]]
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {
                    "role": "user",
                    "content": _TagPrompt.SYSTEM,
                    "images": images,
                }
            ],
        }

        try:
            result = _post_json(f"{self.base_url}/api/chat", payload, TAGGER_TIMEOUT_SECONDS)
        except Exception as err:
            raise RuntimeError(t("tagger_api_error", source="ollama", error=err))

        raw = None
        if isinstance(result, dict) and result.get("message"):
            raw = result["message"].get("content")
        elif isinstance(result, dict) and isinstance(result.get("choices"), list):
            msg = result["choices"][0] if result["choices"] else {}
            if isinstance(msg, dict):
                raw = msg.get("message", {}).get("content")
        elif isinstance(result, dict):
            raw = result.get("response")

        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(t("tagger_api_empty", source="ollama"))

        return _normalize_tags(raw)


class StepFunVisionTagger(BaseTagger):
    def __init__(self, api_key: str, model: str = STEPFUN_MODEL, base_url: str = STEPFUN_API_BASE):
        self.api_key = api_key.strip()
        self.model = model or "step-1v-8k"
        self.base_url = base_url.rstrip("/")

    def tag_clip(self, keyframe_paths: list[str]) -> dict:
        if not self.api_key:
            raise ValueError(t("tagger_missing_key", source="stepfun"))

        content = [
            {"type": "text", "text": _TagPrompt.SYSTEM},
        ]
        for path in keyframe_paths[:TAGGER_MAX_KEYFRAMES]:
            image_data = _read_image_as_base64(path)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{_detect_mime_type(path)};base64,{image_data}"
                    },
                }
            )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
            "response_format": {"type": "json_object"},
        }

        request = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            method="POST",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=TAGGER_TIMEOUT_SECONDS) as response:
                response_text = response.read().decode("utf-8")
            result = json.loads(response_text)
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="ignore") if err.fp else ""
            raise RuntimeError(t("tagger_api_error", source="stepfun", error=f"{err.code} {body}"))
        except Exception as err:
            raise RuntimeError(t("tagger_api_error", source="stepfun", error=err))

        choices = result.get("choices") if isinstance(result, dict) else None
        msg = choices[0] if isinstance(choices, list) and choices else {}
        raw = None
        if isinstance(msg, dict):
            raw = msg.get("message", {}).get("content")

        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(t("tagger_api_empty", source="stepfun"))

        normalized = _normalize_tags(raw)
        if normalized.get("description"):
            return normalized

        return _normalize_tags(result) if isinstance(result, dict) else normalized

    # keep only the concrete implementation above


def get_tagger() -> BaseTagger:
    if TAGGER_BACKEND == "mock":
        return MockTagger()
    if TAGGER_BACKEND == "ollama":
        return OllamaVisionTagger()
    if TAGGER_BACKEND == "stepfun":
        return StepFunVisionTagger(api_key=STEPFUN_API_KEY)
    raise ValueError(f"Unknown tagger backend: {TAGGER_BACKEND}")


def tag_clip(clip_id: int) -> dict:
    with get_connection() as conn:
        keyframes = queries.get_clip_keyframes(conn, clip_id)
        if not keyframes:
            raise ValueError(t("tagger_no_keyframes", clip_id=clip_id))

        tagger = get_tagger()
        keyframe_paths = [k["frame_path"] for k in keyframes]

        tags = tagger.tag_clip(keyframe_paths)
        queries.clear_clip_tags(conn, clip_id)

        for field in [
            "theme", "objects", "scene", "action", "shot", "style", "color",
            "lighting", "mood", "use_case",
        ]:
            values = tags.get(field, [])
            if isinstance(values, str):
                values = [values]
            for value in values:
                if isinstance(value, str):
                    queries.insert_clip_tag(conn, clip_id=clip_id, tag_type=field, tag_value=value, confidence=1.0)

        description = tags.get("description") or t("tagger_description_empty")
        queries.set_clip_description(conn, clip_id=clip_id, description=description)
        return tags
