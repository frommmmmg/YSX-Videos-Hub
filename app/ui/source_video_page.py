from __future__ import annotations

import streamlit as st

from app.db.database import get_connection
from app.db import queries
from app.i18n import t


def render():
    st.header(t("source_title"))
    with get_connection() as conn:
        rows = queries.get_source_videos(conn)

    if not rows:
        st.info(t("source_no_data"))
        return

    for row in rows:
        with st.expander(f"{row['id']} - {row['file_name']}"):
            st.write(t("source_path", path=row["file_path"]))
            st.write(t("source_duration", duration=float(row["duration"] or 0)))
            st.write(t("source_resolution", value=row["resolution"]))
            st.write(t("source_fps", value=row["fps"]))
            st.write(t("source_imported_at", value=row["imported_at"]))
            if row.get("note"):
                st.write(t("source_note", note=row["note"]))
