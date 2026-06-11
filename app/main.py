from __future__ import annotations

import os
import sys
import streamlit as st

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.db.database import init_database
from app.services.file_service import ensure_library_directories
from app.ui.clip_detail_page import render as render_clip_detail
from app.ui.clips_page import render as render_clips
from app.ui.home_page import render as render_home
from app.ui.import_page import render as render_import
from app.ui.settings_page import render as render_settings
from app.ui.source_video_page import render as render_source
from app.i18n import set_locale, t


def main():
    ensure_library_directories()
    init_database()

    if "ui_locale" not in st.session_state:
        set_locale("zh")

    app_title = t("app_title")
    st.set_page_config(page_title=app_title, layout="wide")

    locales = ["zh", "en"]
    current_locale = st.session_state.get("ui_locale", "zh")
    selected_locale = st.sidebar.selectbox(
        t("language_label"),
        options=locales,
        index=locales.index(current_locale),
        format_func=lambda locale: t(f"language_{locale}"),
        key="locale_selector",
    )
    set_locale(selected_locale)
    st.title(t("app_title"))

    page_keys = ["home", "import", "library", "detail", "source", "settings"]
    current_page = st.session_state.get("selected_page", "home")
    if current_page not in page_keys:
        current_page = "home"
    selected_page = st.sidebar.radio(
        t("nav_title"),
        page_keys,
        index=page_keys.index(current_page),
        format_func=lambda page_key: t(f"nav_{page_key}"),
        key="selected_page",
    )

    if selected_page == "home":
        render_home()
    elif selected_page == "import":
        render_import()
    elif selected_page == "library":
        render_clips()
    elif selected_page == "detail":
        render_clip_detail()
    elif selected_page == "source":
        render_source()
    elif selected_page == "settings":
        render_settings()


if __name__ == "__main__":
    main()
