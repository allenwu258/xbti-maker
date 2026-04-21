from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
APP_DIR = BASE_DIR / "app"
STORAGE_DIR = BASE_DIR / "storage"
EXPORTS_DIR = STORAGE_DIR / "exports"
DATABASE_PATH = STORAGE_DIR / "xbti.sqlite3"


def ensure_storage_dirs() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
