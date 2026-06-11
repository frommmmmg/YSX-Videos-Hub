from __future__ import annotations

import streamlit as st

from app.services.video_importer import import_video
from app.services.video_splitter import split_video_fixed
from app.services.keyframe_extractor import extract_keyframes
from app.i18n import t


VIDEO_FILE_TYPES = ["*.mp4 *.mov *.mkv *.avi *.m4v *.webm", "*.*"]


def _choose_video_file() -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.askopenfilename(
            title=t("import_file_dialog_title"),
            filetypes=[(t("import_file_type_video"), VIDEO_FILE_TYPES[0]), (t("import_file_type_all"), VIDEO_FILE_TYPES[1])],
        )
    finally:
        root.destroy()

    return selected or None


def render():
    st.header(t("import_title"))

    if "video_path" not in st.session_state:
        st.session_state["video_path"] = ""

    if st.button(t("import_choose_file_btn")):
        selected_path = _choose_video_file()
        if selected_path:
            st.session_state["video_path"] = selected_path
        else:
            st.warning(t("import_choose_warning"))

    video_path = st.text_input(
        t("import_path_input"),
        key="video_path",
        help=t("import_path_help"),
    )

    if st.button(t("import_submit_btn")):
        try:
            if video_path.strip():
                source_video_id, is_new = import_video(video_path.strip())
            else:
                st.error(t("import_require_path"))
                return

            if is_new:
                st.success(t("import_success", source_video_id=source_video_id))
            else:
                st.warning(t("import_exist", source_video_id=source_video_id))
                if st.button(t("import_reprocess_btn"), key=f"reprocess_{source_video_id}"):
                    clip_ids = split_video_fixed(source_video_id)
                    if not clip_ids:
                        st.warning(t("import_no_new_segments"))
                    else:
                        for cid in clip_ids:
                            try:
                                extract_keyframes(cid)
                            except Exception as err:
                                st.warning(t("import_keyframe_failed", clip_id=cid, error=err))
                    st.success(t("import_reprocess_done"))
                    return

            clip_ids = split_video_fixed(source_video_id)
            st.success(t("import_segments_created", count=len(clip_ids)))
            for cid in clip_ids:
                try:
                    extract_keyframes(cid)
                except Exception as err:
                    st.warning(t("import_keyframe_failed", clip_id=cid, error=err))
            st.success(t("import_keyframe_done"))
        except Exception as err:
            st.error(t("import_error", error=err))
