import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Documents Fast API"
    PROJECT_VERSION: str = "0.8.7"

    # DB settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "postgres")
    DATABASE_URL: str = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/"
        f"{POSTGRES_DB}"
    )

    # RabbitMQ settings
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    MESSAGE_MAX_AGE_MS: int = 12 * 3600 * 1000

    # Filesystem settings
    DATA_STORAGE_PATH: Path = os.getenv("DATA_STORAGE_PATH", "/data")
    PAGES_PATH: Path = Path(DATA_STORAGE_PATH) / "pages"
    UPLOADS_PATH: Path = Path(DATA_STORAGE_PATH) / "uploads"
    UPLOAD_CHUNK_SIZE: int = os.getenv("UPLOAD_CHUNK_SIZE", 1024 * 1024 * 5)

    # Development settings
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", False)
    UNIT_TESTING: bool = os.getenv("UNIT_TESTING", False)


settings = Settings()
