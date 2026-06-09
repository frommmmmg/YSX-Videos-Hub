from __future__ import annotations

import math
import streamlit as st

from app.config.settings import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.services.search_service import search_clips


def render():
    st.header("素材库")
    query = st.text_input("搜索关键词（空格分隔）")
    page_size = st.number_input("每页数量", min_value=1, max_value=MAX_PAGE_SIZE, value=DEFAULT_PAGE_SIZE, step=1)
    page = st.number_input("页码", min_value=1, value=1, step=1)

    clips, total = search_clips(query.strip() if query else None, page=int(page), page_size=int(page_size))
    total_pages = max(1, math.ceil((total or 0) / page_size))
    if int(page) > total_pages:
        page = total_pages
        clips, total = search_clips(query.strip() if query else None, page=int(page), page_size=int(page_size))

    st.caption(f"共 {total} 条，当前第 {page}/{total_pages} 页")

    if not clips:
        st.info("当前没有素材。先去【导入视频】再来看看。")
        return

    rows = list(chunks(clips, 4))
    for row in rows:
        columns = st.columns(len(row))
        for col, clip in zip(columns, row):
            with col:
                st.caption(f"clip #{clip['id']}")
                if clip["thumbnail_path"]:
                    st.image(clip["thumbnail_path"], use_container_width=True)
                st.write(f"时长：{float(clip['clip_duration'] or 0):.2f}s")
                st.write(f"来源：{clip['source_file_name']}")
                st.write(f"时间：{float(clip['source_start_time'] or 0):.2f} - {float(clip['source_end_time'] or 0):.2f}")
                st.write(f"收藏：{'是' if clip['favorite'] else '否'}")
                if st.button("查看详情", key=f"clip_detail_{clip['id']}"):
                    st.session_state["selected_clip_id"] = clip["id"]
                    st.session_state["selected_page"] = "素材详情"
                    st.rerun()


def chunks(items, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]
