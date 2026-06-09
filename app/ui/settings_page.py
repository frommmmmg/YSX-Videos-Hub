from __future__ import annotations

import streamlit as st

from app.config import settings


def render():
    st.header("设置")
    st.subheader("运行参数")
    st.write(f"素材库路径：{settings.LIBRARY_DIR}")
    st.write(f"默认切片时长：{settings.TARGET_CLIP_DURATION}s")
    st.write(f"最短片段：{settings.MIN_CLIP_DURATION}s")
    st.write(f"最长片段：{settings.MAX_CLIP_DURATION}s")
    st.write(f"Tagger 接口：{settings.TAGGER_BACKEND}")
    st.caption("当前版本保留 VLM 接口，未绑定具体模型实现。")
