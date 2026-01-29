from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables"""

    # DATABASE SETTINGS
    MONGO_URI: str = None
    DB_NAME: str = None

    # MongoDB connection pool settings
    MONGO_MAX_POOL_SIZE: int = None
    MONGO_MIN_POOL_SIZE: int = None
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = None

    # LLM SETTINGS (Ollama)
    OLLAMA_URL: str = None
    OLLAMA_TIMEOUT: Optional[int] = None

    # CORS SETTINGS
    CORS_ORIGINS: list[str] = None

    # WEB SEARCH PROVIDER SETTINGS
    # DuckDuckGo (DDG) - Free search engine
    DDG_LIMIT: int = None  # Max results per search
    DDG_TIMEOUT: float = None  # Request timeout in seconds

    # SearXNG - Self-hosted metasearch engine
    SEARXNG_URL: Optional[str] = None  # e.g. http://localhost:8080
    SEARXNG_LIMIT: int = None  # Max results per search
    SEARXNG_TIMEOUT: float = None  # Request timeout in seconds

    # Serper - Google Search API (paid, quota-limited)
    SERPER_URL: str | None = None
    SERPER_API_KEY: str | None = None
    SERPER_LIMIT: int = None  # Max results per search
    SERPER_TOTAL_LIMIT: int = None  # Monthly API quota
    SERPER_TIMEOUT: float = None  # Request timeout in seconds

    # Tavily - Research API (paid, quota-limited)
    TAVILY_URL: str | None = None
    TAVILY_API_KEY: Optional[str] = None
    TAVILY_LIMIT: int = None  # Max results per search
    TAVILY_TIMEOUT: float = None  # Request timeout in seconds
    TAVILY_MONTHLY_LIMIT: int = None  # Monthly API quota

    # WEB EXTRACTION SETTINGS
    # Local extraction - Extract content from URLs without external APIs
    LOCAL_EXTRACT_MAX_CHARS: int = None  # Cap returned text length
    LOCAL_EXTRACT_MAX_BYTES: int = None  # Cap download size (~10 MB)
    LOCAL_EXTRACT_TIMEOUT: float = None  # Request timeout in seconds

    # Tavily extraction - Extract content using Tavily's API
    TAVILY_EXTRACT_MAX_LENGTH: int = None  # Cap extracted text length
    TAVILY_EXTRACT_TIMEOUT: float = None  # Request timeout in seconds

    # CHAT PROMPT SETTINGS
    # These control how much context is included in the prompt
    CHAT_EXTRACT_MAX_CHARS: int = None  # Max chars from URL extraction
    CHAT_PROMPT_MAX_LENGTH: int = None  # Max total prompt length to model
    CHAT_MEMORY_LIMIT: int = None  # Max total memory length to model
    CHAT_WEB_SEARCH_LIMIT: int = None  # Max total web search length to model

    # MEMORY SETTINGS
    MEMORY_MAX_CONTENT_LENGTH: int = None  # Max chars per memory entry
    MEMORY_MIN_ASSISTANT_LENGTH: int = None  # Min chars in assistant response to remember
    MEMORY_MIN_CONVERSATION_LENGTH: int = None  # Min combined user+assistant length to remember

    # SEARCH MEMORY SETTINGS
    SEARCH_MAX_MEMORY_LIMIT: int = None
    SEARCH_MEMORY_MAX_THRESHOLD: float = None

    class Config:
        env_file = '.env'
        case_sensitive = True


settings = Settings()
