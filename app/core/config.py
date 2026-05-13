from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SvoyDom CRM Bot"
    app_env: str = "local"
    app_host: str = Field("0.0.0.0", validation_alias=AliasChoices("APP_HOST", "HOST"))
    app_port: int = Field(8000, validation_alias=AliasChoices("APP_PORT", "PORT"))
    public_base_url: str = "https://example.com"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/svoydom_crm"
    bot_token: str = "replace-with-telegram-bot-token"
    admin_telegram_ids: list[int] = Field(default_factory=list)
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
    cors_origins: list[str] = Field(default_factory=lambda: ["https://svoydom-lugansk.ru"])

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("admin_telegram_ids", mode="before")
    @classmethod
    def parse_int_list(cls, value: str | list[int]) -> list[int]:
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_str_list(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
