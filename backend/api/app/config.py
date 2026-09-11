from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    PROJECT_NAME: str = "ROADSense"
    API_V1_STR: str = "/api"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"

    M1_DATA_PATH: str = os.getenv(
        "M1_DATA_PATH",
        str(PROJECT_ROOT / "data" / "processed" / "m1_output" / "prioritized_detections.csv")
    )

    M2_DATA_PATH: str = os.getenv(
        "M2_DATA_PATH",
        str(PROJECT_ROOT / "data" / "processed" / "m2_output" / "damage_instances.geojson")
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()