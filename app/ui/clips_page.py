from __future__ import annotations

import math
import streamlit as st

from app.config.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.services.search_service import search_clips
from app.i18n import t


def render():
    st.header(t("clips_title"))
    query = st.text_input(t("clips_search_placeholder"))
    page_size = st.number_input(t("clips_page_size"), min_value=1, max_value=MAX_PAGE_SIZE, value=DEFAULT_PAGE_SIZE, step=1)
    page = st.number_input(t("clips_page"), min_value=1, value=1, step=1)

    clips, total = search_clips(query.strip() if query else None, page=int(page), page_size=int(page_size))
    total_pages = max(1, math.ceil((total or 0) / page_size))
    if int(page) > total_pages:
        page = total_pages
        clips, total = search_clips(query.strip() if query else None, page=int(page), page_size=int(page_size))

    st.caption(t("clips_pagination", total=total, page=page, total_pages=total_pages))

    if not clips:
        st.info(t("clips_empty", import_page=t("nav_import")))
        return

    rows = list(chunks(clips, 4))
    for row in rows:
        columns = st.columns(len(row))
        for col, clip in zip(columns, row):
            with col:
                st.caption(f"clip #{clip['id']}")
                if clip["thumbnail_path"]:
                    st.image(clip["thumbnail_path"], use_container_width=True)
                st.write(
                    t(
                        "clips_length",
                        duration=float(clip["clip_duration"] or 0),
                    )
                )
                st.write(
                    t(
                        "clips_source",
                        name=clip["source_file_name"],
                    )
                )
                st.write(
                    t(
                        "clips_time",
                        start=float(clip["source_start_time"] or 0),
                        end=float(clip["source_end_time"] or 0),
                    )
                )
                st.write(
                    t(
                        "clips_favorite",
                        favorite=t("clips_favorite_true") if clip["favorite"] else t("clips_favorite_false"),
                    )
                )
                if st.button(t("clips_detail_btn"), key=f"clip_detail_{clip['id']}"):
                    st.session_state["selected_clip_id"] = clip["id"]
                    st.session_state["selected_page"] = "detail"
                    st.rerun()


def chunks(items, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]
