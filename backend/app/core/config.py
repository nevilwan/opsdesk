"""Application configuration — loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "OpsDesk AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production-use-long-random-string"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://opsdesk:opsdesk@localhost:5432/opsdesk"
    REDIS_URL: str = "redis://localhost:6379/0"

    # ML
    MODELS_DIR: str = "../ml/models"
    DATA_DIR: str = "../data/processed"

    # OpenAI (optional — chatbot degrades gracefully without it)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Anthropic (optional — chatbot degrades gracefully without it)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 1440  # 24h

    # SLA defaults (hours)
    SLA_CRITICAL_HOURS: int = 2
    SLA_HIGH_HOURS: int = 8
    SLA_MEDIUM_HOURS: int = 24
    SLA_LOW_HOURS: int = 72

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
