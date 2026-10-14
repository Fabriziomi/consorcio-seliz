from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Base de Datos (SQLite local para dev MVP / PostgreSQL para producción)
    DATABASE_URL: str = "sqlite+aiosqlite:///./consorcio.db"

    # Seguridad y Autenticación JWT
    JWT_SECRET_KEY: str = "consorcio_seliz_secret_jwt_key_2026_production_safe"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas

    # Cache Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Pasarela WhatsApp Evolution API
    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = "consorcio_api_token_secret"
    EVOLUTION_INSTANCE_NAME: str = "ivana_seliz_whatsapp"

    # Intermediario Omnicanal Chatwoot
    CHATWOOT_API_URL: str = "http://localhost:3000"
    CHATWOOT_API_ACCESS_TOKEN: Optional[str] = None
    CHATWOOT_ACCOUNT_ID: int = 1
    CHATWOOT_INBOX_ID: int = 1

    # NocoDB CRM
    NOCODB_API_URL: str = "http://localhost:8081"
    NOCODB_API_TOKEN: Optional[str] = None

    # Horarios de Atención Ivana Seliz
    OFFICE_HOURS_MF_START: str = "10:00"
    OFFICE_HOURS_MF_END: str = "18:00"
    OFFICE_HOURS_SAT_START: str = "10:00"
    OFFICE_HOURS_SAT_END: str = "13:00"
    QUIET_HOURS_START: str = "00:00"
    QUIET_HOURS_END: str = "07:30"

    # Configuración de Timeouts para VPS / Redes con latencia
    HTTP_CLIENT_TIMEOUT: float = 60.0

    # Debug Rápido
    FAST_DEBUG_MODE: bool = False
    BYPASS_DEBOUNCE_BUFFER: bool = False
    OVERRIDE_SCHEDULE_OFF_HOURS: bool = False


settings = Settings()
