from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Formulario CRM"
    vtiger_base_url: str
    vtiger_username: str
    vtiger_access_key: SecretStr
    vtiger_timeout_seconds: float = 15.0
    vtiger_assigned_user_id: str | None = None
    woo_base_url: str | None = None
    woo_consumer_key: SecretStr | None = None
    woo_consumer_secret: SecretStr | None = None
    woo_api_version: str = "wc/v3"
    woo_timeout_seconds: float = 15.0
    woo_query_string_auth: bool = False

    @field_validator("vtiger_base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("vtiger_base_url must start with http:// or https://")
        return normalized

    @field_validator("vtiger_username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("vtiger_username cannot be empty")
        return normalized

    @field_validator("vtiger_assigned_user_id")
    @classmethod
    def normalize_assigned_user_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("woo_base_url")
    @classmethod
    def validate_woo_base_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().rstrip("/")
        if not normalized:
            return None
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("woo_base_url must start with http:// or https://")
        return normalized

    @field_validator("woo_api_version")
    @classmethod
    def validate_woo_api_version(cls, value: str) -> str:
        normalized = value.strip().strip("/")
        if not normalized:
            raise ValueError("woo_api_version cannot be empty")
        return normalized


@lru_cache
def get_settings() -> Settings:
    return Settings()
