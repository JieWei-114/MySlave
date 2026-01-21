"""
Application Settings and Configuration
Uses pydantic-settings for environment variable management
"""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables"""

    # Database settings
    MONGO_URI: str = 'mongodb://127.0.0.1:27017'
    DB_NAME: str = 'myslave'

    # Ollama settings
    OLLAMA_URL: str = 'http://localhost:11434/api/generate'
    OLLAMA_TIMEOUT: Optional[int] = None

    # CORS settings
    CORS_ORIGINS: list[str] = ['http://localhost:4200', 'http://localhost:8000']

    # MongoDB connection pool settings
    MONGO_MAX_POOL_SIZE: int = 50
    MONGO_MIN_POOL_SIZE: int = 10
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = 5000

    class Config:
        env_file = '.env'
        case_sensitive = True


settings = Settings()
