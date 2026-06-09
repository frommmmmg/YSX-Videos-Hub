from pathlib import Path


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

TAGGER_BACKEND = "mock"

LOG_FILE = LOGS_DIR / "app.log"
