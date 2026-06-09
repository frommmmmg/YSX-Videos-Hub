from __future__ import annotations

def seconds_to_timecode(seconds: float) -> str:
    if seconds is None:
        return "00:00:00.000"
    total_ms = max(0.0, seconds) * 1000.0
    ms = int(round(total_ms)) % 1000
    total_sec = int(total_ms // 1000)
    s = total_sec % 60
    m = (total_sec // 60) % 60
    h = total_sec // 3600
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def timecode_to_seconds(timecode: str) -> float:
    h_str, m_str, rest = timecode.split(":")
    s_str, ms_str = rest.split(".") if "." in rest else (rest, "0")
    return int(h_str) * 3600 + int(m_str) * 60 + int(s_str) + int(ms_str) / 1000.0
