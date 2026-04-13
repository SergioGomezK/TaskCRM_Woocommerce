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
    vtiger_lead_field_product_id: str = "product_id"
    vtiger_lead_field_woo_order_id: str = "woo_order_id"
    vtiger_lead_field_sync_status: str = "sync_status"
    vtiger_lead_field_sync_error: str = "sync_error"
    vtiger_lead_field_student_id_type: str = "student_id_type"
    vtiger_lead_field_student_id_number: str = "student_id_number"
    vtiger_lead_field_student_academic_program: str = "student_academic_program"
    vtiger_sync_pending_value: str = "pending"
    vtiger_sync_processed_value: str = "processed"
    vtiger_sync_failed_value: str = "failed"
    vtiger_sync_batch_limit_default: int = 50
    woo_base_url: str | None = None
    woo_consumer_key: SecretStr | None = None
    woo_consumer_secret: SecretStr | None = None
    woo_api_version: str = "wc/v3"
    woo_timeout_seconds: float = 15.0
    woo_query_string_auth: bool = False
    woo_checkout_path: str = "/checkout/"
    woo_default_country: str = "CO"
    woo_default_payment_method: str = "bacs"
    woo_default_payment_method_title: str = "Transferencia bancaria"
    woo_default_set_paid: bool = False
    integration_api_key: SecretStr | None = None

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

    @field_validator(
        "vtiger_lead_field_product_id",
        "vtiger_lead_field_woo_order_id",
        "vtiger_lead_field_sync_status",
        "vtiger_lead_field_sync_error",
        "vtiger_lead_field_student_id_type",
        "vtiger_lead_field_student_id_number",
        "vtiger_lead_field_student_academic_program",
        "vtiger_sync_pending_value",
        "vtiger_sync_processed_value",
        "vtiger_sync_failed_value",
        "woo_default_payment_method",
        "woo_default_payment_method_title",
    )
    @classmethod
    def normalize_non_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Configuration value cannot be empty")
        return normalized

    @field_validator("vtiger_sync_batch_limit_default")
    @classmethod
    def validate_batch_limit_default(cls, value: int) -> int:
        if value < 1:
            raise ValueError("vtiger_sync_batch_limit_default must be >= 1")
        if value > 500:
            raise ValueError("vtiger_sync_batch_limit_default must be <= 500")
        return value

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

    @field_validator("woo_checkout_path")
    @classmethod
    def validate_checkout_path(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("woo_checkout_path cannot be empty")
        if not normalized.startswith("/"):
            normalized = "/" + normalized
        return normalized

    @field_validator("woo_default_country")
    @classmethod
    def validate_default_country(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 2:
            raise ValueError("woo_default_country must be an ISO-2 country code")
        return normalized


@lru_cache
def get_settings() -> Settings:
    return Settings()
