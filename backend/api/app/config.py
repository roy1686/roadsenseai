from pathlib import Path
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    PROJECT_NAME: str = "ROADSense AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    API_V1_STR: str = "/api/v1"
    LEGACY_API_STR: str = "/api"

    # Database: In production, DATABASE_URL must be a PostgreSQL connection string
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'roadsense.db'}")

    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "roadsense-ai-insecure-dev-secret-key-change-in-prod-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://roadsense-ai.vercel.app",
        "https://*.vercel.app",
        "*"
    ]

    # AI & Copilot (Set GROQ_API_KEY in environment or .env for LLM acceleration)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Vision & ML Inference Parameters
    YOLO_MODEL_PATH: str = str(PROJECT_ROOT / "models" / "road_damage.pt")
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.20
    DEFAULT_IOU_THRESHOLD: float = 0.45
    DEFAULT_SAMPLING_INTERVAL_SEC: float = 1.0
    DEFAULT_BLUR_THRESHOLD: float = 100.0
    MAX_UPLOAD_SIZE_MB: int = 100
    PROCESSING_TIMEOUT_SEC: int = 300

    # Paths
    UPLOAD_TEMP_DIR: str = str(PROJECT_ROOT / "data" / "raw" / "video_uploads")
    PROCESSED_DATA_DIR: str = str(PROJECT_ROOT / "data" / "processed")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def validate_production_db(self):
        if self.ENVIRONMENT.lower() == "production" and os.getenv("STRICT_PROD_DB", "false").lower() == "true":
            if not self.DATABASE_URL or self.DATABASE_URL.startswith("sqlite"):
                raise RuntimeError(
                    "CRITICAL PRODUCTION ERROR: DATABASE_URL must be configured with a valid "
                    "PostgreSQL connection string (e.g. postgresql://user:pass@host:port/db) in production!"
                )

settings = Settings()
settings.validate_production_db()