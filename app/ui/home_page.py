from __future__ import annotations

import streamlit as st

from app.config.settings import LIBRARY_DIR
from app.services.search_service import get_home_stats
from app.i18n import t


def render():
    st.header(t("home_title"))
    stats = get_home_stats()
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(t("home_stat_source_count"), stats.get("source_count", 0))
    col2.metric(t("home_stat_clip_count"), stats.get("clip_count", 0))
    col3.metric(t("home_stat_keyframe_count"), stats.get("keyframe_count", 0))
    col4.metric(t("home_stat_tag_count"), stats.get("tag_count", 0))
    col5.metric(t("home_stat_favorite_count"), stats.get("favorite_count", 0))

    st.markdown(f"{t('home_library_path')}：`{LIBRARY_DIR}`")
