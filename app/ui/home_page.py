from __future__ import annotations

import streamlit as st

from app.config.settings import LIBRARY_DIR
from app.services.search_service import get_home_stats


def render():
    st.header("首页")
    stats = get_home_stats()
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("原视频数量", stats.get("source_count", 0))
    col2.metric("clip 数量", stats.get("clip_count", 0))
    col3.metric("关键帧数量", stats.get("keyframe_count", 0))
    col4.metric("标签数量", stats.get("tag_count", 0))
    col5.metric("收藏数量", stats.get("favorite_count", 0))

    st.markdown(f"素材库路径：`{LIBRARY_DIR}`")
