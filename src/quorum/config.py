import os
from pathlib import Path
from pydantic import BaseModel, Field
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseModel):
    app_name: str = "Quorum AI Expert Council"
    app_version: str = "1.0.0"
    app_env: str = os.getenv("APP_ENV", "development")
    
    # Gemini Configuration
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_temperature: float = 0.4
    gemini_top_p: float = 0.95
    gemini_max_tokens: int = 8192
    
    # Server Configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    
    # File Paths
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "src" / "quorum" / "data"
    excel_catalog_path: Path = BASE_DIR / "EXPERT LIST.xlsx"
    docx_library_path: Path = BASE_DIR / "Expert Council Advice Library Technology and Software Batch 1.docx"

settings = Settings()
