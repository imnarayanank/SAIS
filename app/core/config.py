"""
app/core/config.py
------------------
Application configuration using Pydantic Settings.
Reads from environment variables or .env file.

Set DATABASE_URL in your .env file to connect to PostgreSQL:
  DATABASE_URL=postgresql+psycopg://postgres:secret@localhost:5432/learnable
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Student Academic Intelligence System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "sais-super-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database — PostgreSQL (override via DATABASE_URL in .env)
    DATABASE_URL: str = "postgresql+psycopg://postgres:secret@localhost:5432/learnable"

    # Supabase Auth / PostgreSQL deployment settings
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_OAUTH_REDIRECT_URL: str = ""

    # File uploads
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
