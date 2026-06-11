from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[2]
APP_NAME = "Video Material Library"
LIBRARY_DIR = BASE_DIR / "library_data"

ORIGINALS_DIR = LIBRARY_DIR / "originals"
CLIPS_DIR = LIBRARY_DIR / "clips"
THUMBNAILS_DIR = LIBRARY_DIR / "thumbnails"
KEYFRAMES_DIR = LIBRARY_DIR / "keyframes"
EXPORTS_DIR = LIBRARY_DIR / "exports"
DATABASE_DIR = LIBRARY_DIR / "database"
LOGS_DIR = LIBRARY_DIR / "logs"
TEMP_DIR = LIBRARY_DIR / "temp"

DB_PATH = DATABASE_DIR / "library.db"

FFMPEG_PATH = "ffmpeg"
FFPROBE_PATH = "ffprobe"

MIN_CLIP_DURATION = 2.0
TARGET_CLIP_DURATION = 4.0
MAX_CLIP_DURATION = 8.0

DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 48

TAGGER_BACKEND = os.getenv("TAGGER_BACKEND", "mock").strip().lower()

OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://127.0.0.1:11434").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llava:7b").strip()

STEPFUN_API_BASE = os.getenv("STEPFUN_API_BASE", "https://api.stepfun.com").strip()
STEPFUN_API_KEY = os.getenv("STEPFUN_API_KEY", "").strip()
STEPFUN_MODEL = os.getenv("STEPFUN_MODEL", "step-1v-8k").strip()

TAGGER_TIMEOUT_SECONDS = int(os.getenv("TAGGER_TIMEOUT_SECONDS", "30"))
TAGGER_MAX_KEYFRAMES = int(os.getenv("TAGGER_MAX_KEYFRAMES", "8"))

LOG_FILE = LOGS_DIR / "app.log"
