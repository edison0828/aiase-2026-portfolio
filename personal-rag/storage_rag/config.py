from __future__ import annotations

from io import StringIO
import os
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
DEFAULT_VECTOR_STORE_PATH = ARTIFACTS_DIR / "vector_store.sqlite3"
DEFAULT_HF_CACHE_DIR = ARTIFACTS_DIR / "hf_cache"


@dataclass(slots=True)
class Settings:
    root_dir: Path
    raw_dir: Path
    processed_dir: Path
    vector_store_path: Path
    embedding_provider: str
    embedding_model: str
    chat_api_key: str | None
    chat_base_url: str | None
    default_chat_model: str


def _load_project_env(env_path: Path) -> None:
    if not env_path.exists():
        return

    from dotenv import dotenv_values

    parsed = dotenv_values(stream=StringIO(env_path.read_text(encoding="utf-8-sig")))
    for key, value in parsed.items():
        if key is None or value is None:
            continue
        os.environ.setdefault(key, value)


def load_settings() -> Settings:
    _load_project_env(ROOT_DIR / ".env")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(DEFAULT_HF_CACHE_DIR))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(DEFAULT_HF_CACHE_DIR / "hub"))
    os.environ.setdefault(
        "SENTENCE_TRANSFORMERS_HOME",
        str(DEFAULT_HF_CACHE_DIR / "sentence_transformers"),
    )
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

    vector_store_path = Path(
        os.getenv("VECTOR_STORE_PATH", str(DEFAULT_VECTOR_STORE_PATH))
    )
    if not vector_store_path.is_absolute():
        vector_store_path = ROOT_DIR / vector_store_path

    return Settings(
        root_dir=ROOT_DIR,
        raw_dir=RAW_DIR,
        processed_dir=PROCESSED_DIR,
        vector_store_path=vector_store_path,
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "hashing"),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
        ),
        chat_api_key=os.getenv("RAG_API_KEY"),
        chat_base_url=os.getenv("RAG_BASE_URL"),
        default_chat_model=os.getenv("RAG_CHAT_MODEL", ""),
    )
