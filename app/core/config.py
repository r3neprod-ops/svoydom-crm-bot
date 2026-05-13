import json
from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_env_list(value: str) -> list[str]:
    value = value.strip()
    if not value:
        return []

    if value.startswith("["):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]

    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    app_name: str = "SvoyDom CRM Bot"
    app_env: str = "local"
    app_host: str = Field("0.0.0.0", validation_alias=AliasChoices("APP_HOST", "HOST"))
    app_port: int = Field(8000, validation_alias=AliasChoices("APP_PORT", "PORT"))
    public_base_url: str = "https://example.com"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/svoydom_crm"
    bot_token: str = "replace-with-telegram-bot-token"
    admin_telegram_ids_raw: str = Field("", validation_alias="ADMIN_TELEGRAM_IDS")
    site_webhook_secret: str = Field(
        "replace-with-random-shared-secret",
        validation_alias=AliasChoices("SITE_WEBHOOK_SECRET", "CRM_WEBHOOK_TOKEN", "WEBHOOK_SECRET"),
    )
    telegram_webhook_secret: str = Field(
        "replace-with-random-shared-secret",
        validation_alias=AliasChoices("TELEGRAM_WEBHOOK_SECRET", "WEBHOOK_SECRET"),
    )
    webhook_path: str = Field(
        "/telegram/webhook",
        validation_alias=AliasChoices("WEBHOOK_PATH", "TELEGRAM_WEBHOOK_PATH"),
    )
    telegram_webhook_url: str | None = None
    lead_reminder_minutes: int = 30
    lead_reassign_minutes: int = 60
    cors_origins_raw: str = Field(
        "https://svoydom-lugansk.ru",
        validation_alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def admin_telegram_ids(self) -> list[int]:
        return [int(item) for item in _parse_env_list(self.admin_telegram_ids_raw)]

    @property
    def cors_origins(self) -> list[str]:
        return _parse_env_list(self.cors_origins_raw)


@lru_cache
def get_settings() -> Settings:
    return Settings()
