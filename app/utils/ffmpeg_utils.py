from __future__ import annotations

import subprocess

from app.config.settings import FFMPEG_PATH


def resolve_ffmpeg() -> str:
    return FFMPEG_PATH


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if check and completed.returncode != 0:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {' '.join(str(c) for c in cmd)}\n"
            f"stderr={completed.stderr}"
        )
    return completed
