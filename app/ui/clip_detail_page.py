from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from app.db.database import get_connection
from app.db import queries
from app.services.export_service import export_extended_clip
from app.services.keyframe_extractor import extract_keyframes
from app.services.tagger import tag_clip
from app.utils.timecode import seconds_to_timecode


def render():
    st.header("素材详情")
    clip_id = st.session_state.get("selected_clip_id")
    if not clip_id:
        st.info("请先从素材库点“查看详情”")
        return

    with get_connection() as conn:
        clip = queries.get_clip_by_id(conn, int(clip_id))
        if not clip:
            st.error("素材不存在")
            return
        keyframes = queries.get_clip_keyframes(conn, int(clip_id))
        tags = queries.get_clip_tags(conn, int(clip_id))

    st.video(clip["clip_path"])
    st.subheader(f"clip #{clip['id']}")
    st.write(f"原视频：{clip['source_file_name']}")
    st.write(f"原视频路径：{clip['source_file_path']}")
    st.write(
        f"原视频时间码：{seconds_to_timecode(float(clip['source_start_time'] or 0))} - "
        f"{seconds_to_timecode(float(clip['source_end_time'] or 0))}"
    )
    st.write(f"时长：{float(clip['clip_duration'] or 0):.2f} 秒")
    st.write(f"描述：{clip['description'] or '（未识别）'}")
    if clip.get("note"):
        st.warning(f"处理备注：{clip['note']}")

    st.markdown("### 关键帧")
    cols = st.columns(min(4, len(keyframes) or 1))
    for idx, frame in enumerate(keyframes):
        with cols[idx % len(cols)]:
            st.image(frame["frame_path"], caption=f"{frame['frame_role']}({frame['frame_order']})", use_container_width=True)

    st.markdown("### 标签")
    if tags:
        by_type = {}
        for t in tags:
            by_type.setdefault(t["tag_type"], []).append(t["tag_value"])
        for tag_type, values in by_type.items():
            st.markdown(f"**{tag_type}**: {'，'.join(values)}")
    else:
        st.info("暂无标签")

    if st.button("重新抽取关键帧"):
        try:
            extract_keyframes(clip["id"])
            st.success("关键帧已重新生成")
            st.rerun()
        except Exception as err:
            st.error(f"关键帧失败：{err}")

    if st.button("重新AI识别（先Mock）"):
        try:
            tag_clip(clip["id"])
            st.success("标签已更新")
            st.rerun()
        except Exception as err:
            st.error(f"识别失败：{err}")

    st.markdown("### 延展导出")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("前后各延展1秒", key="ext1"):
            _do_export(int(clip["id"]), 1, 1, "copy")
    with col2:
        if st.button("前后各延展3秒", key="ext3"):
            _do_export(int(clip["id"]), 3, 3, "copy")
    with col3:
        if st.button("前后各延展5秒", key="ext5"):
            _do_export(int(clip["id"]), 5, 5, "copy")

    before = st.number_input("前延展秒数", min_value=0.0, value=0.0, step=0.5, key="before")
    after = st.number_input("后延展秒数", min_value=0.0, value=0.0, step=0.5, key="after")
    if st.button("自定义延展导出"):
        _do_export(int(clip["id"]), before, after, "copy")

    st.markdown("### 相邻素材")
    prev_id = clip.get("prev_clip_id")
    next_id = clip.get("next_clip_id")
    c1, c2 = st.columns(2)
    with c1:
        if prev_id:
            if st.button("上一段", key=f"prev_{clip_id}"):
                st.session_state["selected_clip_id"] = prev_id
                st.rerun()
    with c2:
        if next_id:
            if st.button("下一段", key=f"next_{clip_id}"):
                st.session_state["selected_clip_id"] = next_id
                st.rerun()


def _do_export(clip_id: int, before_seconds: float, after_seconds: float, mode: str):
    try:
        path = export_extended_clip(clip_id, before_seconds, after_seconds, mode)
        st.success(f"导出完成：{path}")
        if path:
            st.code(path)
            if st.button("打开导出文件", key=f"open_{clip_id}_{before_seconds}_{after_seconds}"):
                os.startfile(str(Path(path).parent))
    except Exception as err:
        st.error(f"导出失败：{err}")
