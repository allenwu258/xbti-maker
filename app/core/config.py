import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
APP_DIR = BASE_DIR / "app"
STORAGE_DIR = BASE_DIR / "storage"
EXPORTS_DIR = STORAGE_DIR / "exports"
DATABASE_PATH = STORAGE_DIR / "xbti.sqlite3"


def ensure_storage_dirs() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_ark_api_key() -> str:
    return os.getenv("ARK_API_KEY", "").strip()


def get_ark_base_url() -> str:
    return os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")


def get_ark_responses_url() -> str:
    path = os.getenv("ARK_RESPONSES_PATH", "/responses").strip()
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{get_ark_base_url()}{path}"


def get_ark_model_id() -> str:
    return os.getenv("ARK_MODEL_ID", "doubao-seed-1-6-251015").strip()


def get_ark_reasoning_effort() -> str:
    return os.getenv("ARK_REASONING_EFFORT", "high").strip() or "high"


def ark_enabled() -> bool:
    return bool(get_ark_api_key())
