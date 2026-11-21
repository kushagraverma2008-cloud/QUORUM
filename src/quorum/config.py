import os
from pathlib import Path

from pydantic import BaseModel

try:
    from dotenv import load_dotenv

    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseModel):
    app_name: str = "Quorum AI Expert Council"
    app_version: str = "1.1.0"
    app_env: str = os.getenv("APP_ENV", "production")
    debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1")

    # Gemini Configuration
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_fallback_model: str = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.0-flash")
    gemini_temperature: float = 0.4
    gemini_top_p: float = 0.95
    gemini_max_tokens: int = 8192

    # Concurrency and Cache
    llm_concurrency: int = int(os.getenv("LLM_CONCURRENCY", "4"))
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "25.0"))
    cache_dir: Path = BASE_DIR / ".cache"

    # Server Configuration
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")

    # Upload and Input Limits
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "10"))
    max_brief_length: int = int(os.getenv("MAX_BRIEF_LENGTH", "5000"))

    # File Paths
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "src" / "quorum" / "data"
    distilled_dir: Path = BASE_DIR / "data" / "distilled_profiles"


settings = Settings()
