"""Application configuration via environment variables."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    secret_key: str = "dev-secret-key-change-in-production"
    database_url: str = "sqlite:///./risklens.db"
    model_dir: str = "./models"
    data_dir: str = "./data"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    # Risk thresholds (configurable)
    low_risk_threshold: float = 40.0
    medium_risk_threshold: float = 70.0

    # File upload limits
    max_upload_size_mb: int = 10
    max_csv_rows: int = 10000

    model_config = {"env_file": ".env", "extra": "ignore"}

    @field_validator("model_dir", "data_dir", mode="before")
    @classmethod
    def ensure_dir_exists(cls, v: str) -> str:
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
