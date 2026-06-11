from __future__ import annotations

import streamlit as st

from app.config import settings
from app.i18n import t


def render():
    st.header(t("settings_title"))
    st.subheader(t("settings_runtime_title"))
    st.write(t("settings_library_path", path=settings.LIBRARY_DIR))
    st.write(t("settings_target_duration", value=settings.TARGET_CLIP_DURATION))
    st.write(t("settings_min_duration", value=settings.MIN_CLIP_DURATION))
    st.write(t("settings_max_duration", value=settings.MAX_CLIP_DURATION))
    st.write(t("settings_tagger_backend", value=settings.TAGGER_BACKEND))
    if settings.TAGGER_BACKEND == "ollama":
        st.write(t("settings_tagger_endpoint", value=settings.OLLAMA_API_BASE))
        st.write(t("settings_tagger_model", value=settings.OLLAMA_MODEL))
        st.caption(t("settings_tagger_note_ollama"))
    elif settings.TAGGER_BACKEND == "stepfun":
        st.write(t("settings_tagger_endpoint", value=settings.STEPFUN_API_BASE))
        st.write(t("settings_tagger_model", value=settings.STEPFUN_MODEL))
        st.write(t("settings_tagger_api_key", value=bool(settings.STEPFUN_API_KEY)))
        st.caption(t("settings_tagger_note_stepfun"))
    st.caption(t("settings_capability_note"))
