from __future__ import annotations

import streamlit as st

from app.services.video_importer import import_video
from app.services.video_splitter import split_video_fixed
from app.services.keyframe_extractor import extract_keyframes


VIDEO_FILE_TYPES = [
    ("视频文件", "*.mp4 *.mov *.mkv *.avi *.m4v *.webm"),
    ("所有文件", "*.*"),
]


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
            title="选择视频文件",
            filetypes=VIDEO_FILE_TYPES,
        )
    finally:
        root.destroy()

    return selected or None


def render():
    st.header("导入视频")

    if "video_path" not in st.session_state:
        st.session_state["video_path"] = ""

    if st.button("选择视频文件"):
        selected_path = _choose_video_file()
        if selected_path:
            st.session_state["video_path"] = selected_path
        else:
            st.warning("没有选择文件，或当前环境无法打开系统文件选择框。")

    video_path = st.text_input(
        "视频路径",
        key="video_path",
        help="可以点击上方按钮选择，也可以手动粘贴本地视频绝对路径",
    )

    if st.button("导入视频"):
        try:
            if video_path.strip():
                source_video_id, is_new = import_video(video_path.strip())
            else:
                st.error("请先选择视频文件，或输入视频路径")
                return

            if is_new:
                st.success(f"导入成功，source_video_id={source_video_id}")
            else:
                st.warning(f"该文件已导入过，source_video_id={source_video_id}")
                if st.button("重新生成切片与关键帧", key=f"reprocess_{source_video_id}"):
                    clip_ids = split_video_fixed(source_video_id)
                    if not clip_ids:
                        st.warning("未生成新的切片（可能源视频已全部处理过，或处理失败）。")
                    else:
                        for cid in clip_ids:
                            try:
                                extract_keyframes(cid)
                            except Exception as err:
                                st.warning(f"clip {cid} 关键帧提取失败：{err}")
                    st.success("重新处理完成")
                    return

            clip_ids = split_video_fixed(source_video_id)
            st.success(f"已生成 {len(clip_ids)} 段切片")
            for cid in clip_ids:
                try:
                    extract_keyframes(cid)
                except Exception as err:
                    st.warning(f"clip {cid} 关键帧提取失败：{err}")
            st.success("完成关键帧处理")
        except Exception as err:
            st.error(f"导入失败：{err}")
