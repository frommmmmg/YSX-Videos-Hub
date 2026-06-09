from __future__ import annotations

import os
import sys
import streamlit as st

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.config.settings import APP_NAME
from app.db.database import init_database
from app.services.file_service import ensure_library_directories
from app.ui.clip_detail_page import render as render_clip_detail
from app.ui.clips_page import render as render_clips
from app.ui.home_page import render as render_home
from app.ui.import_page import render as render_import
from app.ui.settings_page import render as render_settings
from app.ui.source_video_page import render as render_source


def main():
    ensure_library_directories()
    init_database()

    st.set_page_config(page_title=APP_NAME, layout="wide")
    st.title(APP_NAME)

    menu = ["首页", "导入视频", "素材库", "素材详情", "原视频", "设置"]
    selected = st.sidebar.radio("导航", menu, index=0, key="selected_page")

    if selected == "首页":
        render_home()
    elif selected == "导入视频":
        render_import()
    elif selected == "素材库":
        render_clips()
    elif selected == "素材详情":
        render_clip_detail()
    elif selected == "原视频":
        render_source()
    elif selected == "设置":
        render_settings()


if __name__ == "__main__":
    main()
