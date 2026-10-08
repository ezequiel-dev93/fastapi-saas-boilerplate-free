from typing import List, Optional, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI SaaS Boilerplate"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars-long"

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:4321",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Database
    DATABASE_URL: str = "sqlite:///./saas.db"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID: str = ""
    STRIPE_API_VERSION: str = "2026-08-26.dahlia"

    # AWS Cognito
    AWS_REGION: str = "us-east-1"
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_APP_CLIENT_ID: str = ""

    # AWS SES
    SES_FROM_EMAIL: str = "noreply@example.com"

    # SMTP / Mailpit (Local development email)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    USE_DEV_SMTP: bool = True

    # Redis & Worker
    REDIS_URL: str = "redis://localhost:6379/0"

    # Rate Limiting (SlowAPI)
    RATE_LIMIT_DEFAULT: str = "100/minute"
    ENABLE_RATE_LIMIT: bool = True

    # AI Engine (Pilar 1 - Streaming SSE & Multi-Provider)
    AI_PROVIDER: str = "mock"  # "mock", "openai", "gemini", "claude"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    AI_DEFAULT_MODEL: Optional[str] = None
    AI_ALLOWED_MODELS: List[str] = [
        "gpt-4o",
        "gpt-4o-mini",
        "o3-mini",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet",
        "claude-3-5-haiku-20241022",
        "claude-3-5-haiku",
        "claude-3-opus-20240229",
        "mock-chat",
    ]
    AI_MAX_MESSAGES: int = 50
    AI_MAX_INPUT_CHARS: int = 16000
    AI_MAX_OUTPUT_TOKENS: int = 4096
    AI_SSE_KEEPALIVE_SECONDS: int = 15

    @field_validator("AI_PROVIDER")
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        provider = v.lower().strip()
        if provider not in ("mock", "openai", "gemini", "claude", "anthropic"):
            raise ValueError(
                f"AI_PROVIDER desconocido: '{v}'. Opciones válidas: 'mock', 'openai', 'gemini', 'claude'."
            )
        return provider


    @model_validator(mode="after")
    def validate_production_ai_provider(self) -> "Settings":
        if self.ENVIRONMENT == "production" and self.AI_PROVIDER == "mock":
            raise ValueError(
                "AI_PROVIDER='mock' está estrictamente prohibido en producción (ENVIRONMENT='production')."
            )
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")


settings = Settings()
