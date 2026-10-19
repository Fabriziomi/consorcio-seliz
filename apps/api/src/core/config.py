from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    DATABASE_URL: str = "sqlite+aiosqlite:///./consorcio.db"

    JWT_SECRET_KEY: str = "consorcio_seliz_secret_jwt_key_2026_production_safe"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    REDIS_URL: str = "redis://localhost:6379/0"

    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = "consorcio_api_token_secret"
    EVOLUTION_INSTANCE_NAME: str = "ivana_seliz_whatsapp"
    WEBHOOK_SECRET_TOKEN: str = "consorcio_seliz_webhook_secret_2026"
    ENABLE_WEBHOOK_AUTH: bool = True

    OFFICE_HOURS_MF_START: str = "10:00"
    OFFICE_HOURS_MF_END: str = "18:00"
    OFFICE_HOURS_SAT_START: str = "10:00"
    OFFICE_HOURS_SAT_END: str = "13:00"
    QUIET_HOURS_START: str = "00:00"
    QUIET_HOURS_END: str = "07:30"

    ADMIN_TELEFONO_GUARDIA: Optional[str] = None
    ADMIN_EMAIL_COBRANZAS: Optional[str] = None
    ADMIN_TELEFONO_CONTACTO: Optional[str] = None
    DEFAULT_PAUTAS_MUDANZA: Optional[str] = None

    HTTP_CLIENT_TIMEOUT: float = 60.0

    OPENROUTER_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai"
    JEV_MODEL: str = "typesafe/jev-1.14"
    GEMINI_FALLBACK_MODEL: str = "google/gemini-2.5-flash"
    GROQ_API_KEY: Optional[str] = None
    GROQ_KEY: Optional[str] = None

    CONFIDENCE_THRESHOLD: float = 0.55
    DECISION_TIMEOUT_SECONDS: float = 5.0
    AUDIO_TIMEOUT_SECONDS: float = 3.0
    SESSION_TTL_MINUTES: int = 120
    TAKEOVER_TTL_HOURS: int = 12
    COOLDOWN_MINUTES: int = 5
    MAX_ONBOARDING_RETRIES: int = 2
    BOT_SHADOW_MODE: bool = False
    BOT_GLOBAL_ENABLED: bool = True

    FAST_DEBUG_MODE: bool = False
    BYPASS_DEBOUNCE_BUFFER: bool = False
    OVERRIDE_SCHEDULE_OFF_HOURS: bool = False


settings = Settings()
