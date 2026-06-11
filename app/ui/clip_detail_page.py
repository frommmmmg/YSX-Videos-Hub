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
from app.i18n import t


def render():
    st.header(t("detail_title"))
    clip_id = st.session_state.get("selected_clip_id")
    if not clip_id:
        st.info(t("detail_select_hint"))
        return

    with get_connection() as conn:
        clip = queries.get_clip_by_id(conn, int(clip_id))
        if not clip:
            st.error(t("detail_not_found"))
            return
        keyframes = queries.get_clip_keyframes(conn, int(clip_id))
        tags = queries.get_clip_tags(conn, int(clip_id))

    st.video(clip["clip_path"])
    st.subheader(f"clip #{clip['id']}")
    st.write(t("detail_source_name", name=clip["source_file_name"]))
    st.write(t("detail_source_path", path=clip["source_file_path"]))
    st.write(
        t(
            "detail_timecode",
            start=seconds_to_timecode(float(clip["source_start_time"] or 0)),
            end=seconds_to_timecode(float(clip["source_end_time"] or 0)),
        )
    )
    st.write(t("detail_duration", duration=float(clip["clip_duration"] or 0)))
    st.write(
        t(
            "detail_description",
            description=clip["description"] or t("detail_description_empty"),
        )
    )
    if clip.get("note"):
        st.warning(t("detail_note", note=clip["note"]))

    st.markdown(t("detail_keyframes_title"))
    cols = st.columns(min(4, len(keyframes) or 1))
    for idx, frame in enumerate(keyframes):
        with cols[idx % len(cols)]:
            st.image(frame["frame_path"], caption=f"{frame['frame_role']}({frame['frame_order']})", use_container_width=True)

    st.markdown(t("detail_tags_title"))
    if tags:
        by_type = {}
        for t in tags:
            by_type.setdefault(t["tag_type"], []).append(t["tag_value"])
        for tag_type, values in by_type.items():
            st.markdown(f"**{tag_type}**: {'，'.join(values)}")
    else:
        st.info(t("detail_no_tags"))

    if st.button(t("detail_reextract_btn")):
        try:
            extract_keyframes(clip["id"])
            st.success(t("detail_reextract_ok"))
            st.rerun()
        except Exception as err:
            st.error(t("detail_reextract_error", error=err))

    if st.button(t("detail_ai_btn")):
        try:
            tag_clip(clip["id"])
            st.success(t("detail_ai_ok"))
            st.rerun()
        except Exception as err:
            st.error(t("detail_ai_error", error=err))

    st.markdown(t("detail_export_title"))
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(t("detail_export_1"), key="ext1"):
            _do_export(int(clip["id"]), 1, 1, "copy")
    with col2:
        if st.button(t("detail_export_3"), key="ext3"):
            _do_export(int(clip["id"]), 3, 3, "copy")
    with col3:
        if st.button(t("detail_export_5"), key="ext5"):
            _do_export(int(clip["id"]), 5, 5, "copy")

    before = st.number_input(t("detail_export_before"), min_value=0.0, value=0.0, step=0.5, key="before")
    after = st.number_input(t("detail_export_after"), min_value=0.0, value=0.0, step=0.5, key="after")
    if st.button(t("detail_export_custom")):
        _do_export(int(clip["id"]), before, after, "copy")

    st.markdown(t("detail_adjacent_title"))
    prev_id = clip.get("prev_clip_id")
    next_id = clip.get("next_clip_id")
    c1, c2 = st.columns(2)
    with c1:
        if prev_id:
            if st.button(t("detail_prev"), key=f"prev_{clip_id}"):
                st.session_state["selected_clip_id"] = prev_id
                st.rerun()
    with c2:
        if next_id:
            if st.button(t("detail_next"), key=f"next_{clip_id}"):
                st.session_state["selected_clip_id"] = next_id
                st.rerun()


def _do_export(clip_id: int, before_seconds: float, after_seconds: float, mode: str):
    try:
        path = export_extended_clip(clip_id, before_seconds, after_seconds, mode)
        st.success(t("detail_export_done", path=path))
        if path:
            st.code(path)
            if st.button(t("detail_export_open"), key=f"open_{clip_id}_{before_seconds}_{after_seconds}"):
                os.startfile(str(Path(path).parent))
    except Exception as err:
        st.error(t("detail_export_error", error=err))
