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

    # ============================================================
    # CENTRALIZED LIMIT SYSTEM
    # ============================================================
    # All limits defined once, used consistently across all services

    # --- WEB SEARCH LIMITS ---
    # How many results each provider fetches (per single search call)
    WEB_SEARCH_RESULTS_PER_PROVIDER: int = 10

    # Total limit for "advance search" (distributed across all enabled providers)
    WEB_SEARCH_ADVANCE_TOTAL: int = 40

    # How many results shown in final prompt (filtered from provider results)
    CHAT_WEB_RESULTS_LIMIT: int = 10

    # Max characters per web result snippet in prompt
    CHAT_WEB_SNIPPET_MAX_CHARS: int = 800

    # Total web search content allowed in prompt
    CHAT_WEB_TOTAL_MAX_CHARS: int = 6000

    # --- MEMORY LIMITS ---
    # How many memories to search/retrieve
    MEMORY_SEARCH_LIMIT: int = 10

    # Minimum similarity threshold for memory matching
    MEMORY_SEARCH_THRESHOLD: float = 0.3

    # How many memories shown in final prompt
    CHAT_MEMORY_RESULTS_LIMIT: int = 10

    # Max characters per memory item
    MEMORY_MAX_CHARS_PER_ITEM: int = 500

    # Total memory content allowed in prompt
    CHAT_MEMORY_TOTAL_MAX_CHARS: int = 3000

    # --- CONVERSATION HISTORY LIMITS ---
    # How many recent messages to include
    CHAT_HISTORY_LIMIT: int = 10

    # Max characters per message in history
    CHAT_HISTORY_MAX_CHARS_PER_MSG: int = 500

    # Total history content allowed in prompt
    CHAT_HISTORY_TOTAL_MAX_CHARS: int = 5000

    # Total history content use for review
    CHAT_HISTORY_MAX_ASSISTANT_CONTEXT: int = 5

    # --- FILE UPLOAD LIMITS ---
    # Max file size for upload (in MB)
    FILE_UPLOAD_MAX_SIZE_MB: int = 10

    # Max characters extracted from file (at extraction time)
    FILE_UPLOAD_MAX_CHARS: int = 50000

    # Max file content shown in prompt
    CHAT_FILE_CONTENT_MAX_CHARS: int = 30000

    # --- URL EXTRACTION LIMITS ---
    # Max characters from URL extraction
    CHAT_EXTRACT_MAX_CHARS: int = 15000

    # Total extracted content allowed in prompt
    CHAT_EXTRACT_TOTAL_MAX_CHARS: int = 8000

    # --- OVERALL PROMPT LIMIT ---
    # Final safety limit for entire prompt sent to model
    CHAT_PROMPT_MAX_TOTAL_CHARS: int = 100000

    # --- FEATURES ---
    CHAT_ENABLE_RESULT_RANKING: bool = True

    # ============================================================
    # PROVIDER-SPECIFIC SETTINGS
    # ============================================================
    # DuckDuckGo (DDG) - Free search engine
    DDG_TIMEOUT: float = None
    DDG_LIMIT: str | None = None

    # SearXNG - Self-hosted metasearch engine
    SEARXNG_URL: Optional[str] = None
    SEARXNG_TIMEOUT: float = None
    SEARXNG_LIMIT: str | None = None

    # Serper - Google Search API (paid, quota-limited)
    SERPER_URL: str | None = None
    SERPER_API_KEY: str | None = None
    SERPER_TOTAL_LIMIT: int = None  # Monthly API quota
    SERPER_TIMEOUT: float = None

    # Tavily - Research API (paid, quota-limited)
    TAVILY_URL: str | None = None
    TAVILY_API_KEY: Optional[str] = None
    TAVILY_TIMEOUT: float = None
    TAVILY_MONTHLY_LIMIT: int = None  # Monthly API quota

    # WEB EXTRACTION SETTINGS
    LOCAL_EXTRACT_MAX_CHARS: int = None
    LOCAL_EXTRACT_MAX_BYTES: int = None
    LOCAL_EXTRACT_TIMEOUT: float = None

    TAVILY_EXTRACT_MAX_LENGTH: int = None
    TAVILY_EXTRACT_TIMEOUT: float = None

    # ============================================================
    # MEMORY AUTO-SAVE SETTINGS
    # ============================================================
    MEMORY_MAX_CONTENT_LENGTH: int = None  # Max chars per memory entry
    MEMORY_MIN_ASSISTANT_LENGTH: int = None  # Min chars in assistant response to remember
    MEMORY_MIN_CONVERSATION_LENGTH: int = None  # Min combined user+assistant length to remember

    # ============================================================
    # SYSTEM INSTRUCTIONS
    # ============================================================
    CHAT_SYSTEM_INSTRUCTIONS: str = """
SYSTEM INSTRUCTIONS:
You are a helpful, reliable AI assistant.

General rules:
- Answer the user directly and clearly.
- Use information from web search, URL extraction, files, and memory when provided.
- If information is incomplete or uncertain, say so honestly.

You MAY generate internal reasoning.
- This reasoning is stored separately and is NEVER shown to the user
- unless explicitly requested by the UI.

When web search results are provided:
- Synthesize information from multiple sources.
- Prefer authoritative and recent sources.
- Cite sources in plain text when relevant.

When file content is provided:
- Use the file as a primary source.
- Reference specific sections when helpful.
- Ask clarifying questions if needed.

When memory is provided:
- Use it only when relevant.
- Maintain conversation continuity.

Style:
- Be concise but thorough.
- Use markdown only when it improves readability.
""".strip()

    class Config:
        env_file = '.env'
        case_sensitive = True


settings = Settings()
