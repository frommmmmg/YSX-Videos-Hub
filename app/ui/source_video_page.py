from __future__ import annotations

import streamlit as st

from app.db.database import get_connection
from app.db import queries


def render():
    st.header("原视频")
    with get_connection() as conn:
        rows = queries.get_source_videos(conn)

    if not rows:
        st.info("还没有导入原视频")
        return

    for row in rows:
        with st.expander(f"{row['id']} - {row['file_name']}"):
            st.write(f"路径：{row['file_path']}")
            st.write(f"时长：{float(row['duration'] or 0):.2f}s")
            st.write(f"分辨率：{row['resolution']}")
            st.write(f"fps：{row['fps']}")
            st.write(f"导入时间：{row['imported_at']}")
            if row.get("note"):
                st.write(f"处理备注：{row['note']}")
