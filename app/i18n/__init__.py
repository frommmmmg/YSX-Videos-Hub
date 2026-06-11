from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_LOCALE = "zh"
AVAILABLE_LOCALES = ("zh", "en")


def get_locale() -> str:
    lang = st.session_state.get("ui_locale", DEFAULT_LOCALE)
    if lang in AVAILABLE_LOCALES:
        return lang
    return DEFAULT_LOCALE


def set_locale(locale: str) -> None:
    if locale in AVAILABLE_LOCALES:
        st.session_state["ui_locale"] = locale


def _locale_file(locale: str) -> Path:
    return BASE_DIR / f"messages_{locale}.json"


@lru_cache(maxsize=8)
def _load_messages(locale: str) -> dict[str, str]:
    path = _locale_file(locale)
    if not path.exists():
        path = _locale_file(DEFAULT_LOCALE)
    with path.open("r", encoding="utf-8") as fh:
        payload: dict[str, Any] = json.load(fh)
    return {str(k): str(v) for k, v in payload.items()}


def t(key: str, locale: str | None = None, **kwargs: Any) -> str:
    resolved_locale = locale or get_locale()
    messages = _load_messages(resolved_locale)
    template = messages.get(key) or _load_messages(DEFAULT_LOCALE).get(key) or key
    return template.format(**kwargs) if kwargs else template
    messages = _load_messages(locale)
    template = messages.get(key) or _load_messages(DEFAULT_LOCALE).get(key) or key
    return template.format(**kwargs) if kwargs else template
