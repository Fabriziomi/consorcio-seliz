from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class ChatbotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    ENV: str = "development"
    REDIS_URL: str = "redis://localhost:6379/0"
    API_URL: str = "http://localhost:8000"
    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = "consorcio_api_token_secret"
    EVOLUTION_INSTANCE_NAME: str = "ivana_seliz_whatsapp"

    # Horarios de Atención Ivana Seliz
    OFFICE_HOURS_MF_START: str = "10:00"
    OFFICE_HOURS_MF_END: str = "18:00"
    OFFICE_HOURS_SAT_START: str = "10:00"
    OFFICE_HOURS_SAT_END: str = "13:00"
    QUIET_HOURS_START: str = "00:00"
    QUIET_HOURS_END: str = "07:30"

    # Debounce
    DEBOUNCE_SECONDS: int = 12
    DEBOUNCE_JITTER_SECONDS: int = 3

    # Switches de Debug Rápido
    FAST_DEBUG_MODE: bool = False
    BYPASS_DEBOUNCE_BUFFER: bool = False
    OVERRIDE_SCHEDULE_OFF_HOURS: bool = False


settings = ChatbotSettings()
