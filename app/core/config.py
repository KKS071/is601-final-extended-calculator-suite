# File: app/core/config.py
# Purpose: Application settings loaded from environment variables or .env file.
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL:     str = "postgresql://postgres:postgres@localhost:5432/fastapi_db"
    TEST_DATABASE_URL: Optional[str] = None

    JWT_SECRET_KEY:         str = "your-super-secret-key-change-this-in-production"
    JWT_REFRESH_SECRET_KEY: str = "your-refresh-secret-key-change-this-in-production"
    ALGORITHM:              str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS:   int = 7

    BCRYPT_ROUNDS: int = 12
    CORS_ORIGINS:  List[str] = ["*"]

    class Config:
        env_file      = ".env"
        case_sensitive = True


settings = Settings()


@lru_cache()
def get_settings() -> Settings:
    return Settings()
