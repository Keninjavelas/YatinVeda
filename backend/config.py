"""Application configuration for YatinVeda backend."""

from typing import List
import os


class Settings:
    PROJECT_NAME: str = "YatinVeda API"
    VERSION: str = "1.0.0"
    RELOAD: bool = os.getenv("RELOAD", "false").lower() == "true"

    # CORS – read from env, default to localhost for dev safety
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        raw = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://localhost")
        return [o.strip() for o in raw.split(",") if o.strip()]

    # ── LLM / AI Assistant ─────────────────────────────────
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "local")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
    LOCAL_LLM_BASE_URL: str = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434")
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "llama3.1:8b-instruct-q4_K_M")

    # ── Email ───────────────────────────────────────────────
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "mock")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@yatinveda.local")
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # ── Payments – Razorpay ────────────────────────────────
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")


settings = Settings()

