from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "celiacwriteoff.db"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".webp"}


def ensure_storage_dirs() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def upload_path(item_id: str, extension: str) -> Path:
    return UPLOADS_DIR / f"{item_id}{extension}"


def find_upload_file(item_id: str) -> Path | None:
    matches = list(UPLOADS_DIR.glob(f"{item_id}.*"))
    return matches[0] if matches else None


def delete_file(path: str | None) -> None:
    if not path:
        return
    Path(path).unlink(missing_ok=True)
