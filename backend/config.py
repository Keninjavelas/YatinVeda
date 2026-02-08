"""Application configuration for YatinVeda backend.

Minimal settings object used by FastAPI app and CORS.
"""

from typing import List
import os


class Settings:
    PROJECT_NAME: str = "YatinVeda API"
    VERSION: str = "0.1.0"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    RELOAD: bool = True
    
    # LLM Configuration (AI Assistant)
    # Supported providers: "openai", "anthropic", "local"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "local")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
    
    # Local LLM Configuration (Ollama)
    LOCAL_LLM_BASE_URL: str = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434")
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "llama3.1:8b-instruct-q4_K_M")
    
    # Email Configuration (Local Development)
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "mock")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@yatinveda.local")
    
    # SMTP Configuration (for local development)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "1025"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "false").lower() == "true"


settings = Settings()

