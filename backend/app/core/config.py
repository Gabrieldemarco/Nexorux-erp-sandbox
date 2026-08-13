"""Application settings with secret-file and list helpers."""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_file_secret(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    value = p.read_text(encoding="utf-8").strip()
    return value or None


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "NEXORUX ERP"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nexorux:nexorux123@localhost:5432/nexorux_dev"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    SECRET_KEY_FILE: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    LOCKOUT_USE_REDIS: bool = True
    LOCKOUT_MAX_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15
    RLS_TENANT_CONTEXT_ENABLED: bool = False
    STOCK_ALLOW_NEGATIVE: bool = False
    TRUSTED_HOSTS: str = "localhost,127.0.0.1,nexorux-erp.local"

    # CORS — JSON list or comma-separated string
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    # Password recovery / email
    # EMAIL_BACKEND: smtp | outbox (outbox writes to STORAGE_PATH/mail_outbox)
    EMAIL_BACKEND: str = "smtp"
    SMTP_ENABLED: bool = False
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_PASSWORD_FILE: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    PASSWORD_RESET_URL_BASE: str = "http://localhost:3000/recover-password"

    # DGI Integration
    DGI_ENVIRONMENT: str = "testing"
    DGI_WS_URL: Optional[str] = None
    DGI_CERT_PATH: Optional[str] = None
    DGI_KEY_PATH: Optional[str] = None
    DGI_KEY_PASSWORD: Optional[str] = None
    CFE_XSD_PATH: Optional[str] = None
    CFE_XSD_VALIDATION_REQUIRED: bool = False

    # WooCommerce
    WOOCOMMERCE_URL: Optional[str] = None
    WOOCOMMERCE_CONSUMER_KEY: Optional[str] = None
    WOOCOMMERCE_CONSUMER_SECRET: Optional[str] = None
    WOOCOMMERCE_WEBHOOK_SECRET: Optional[str] = None

    # Storage
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "./storage"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if value is None or value == "":
            return ["http://localhost:3000", "http://localhost:5173"]
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                import json

                return json.loads(text)
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

    @model_validator(mode="after")
    def load_secret_files(self):
        file_key = _read_file_secret(self.SECRET_KEY_FILE)
        if file_key:
            self.SECRET_KEY = file_key
        smtp_pass = _read_file_secret(self.SMTP_PASSWORD_FILE)
        if smtp_pass:
            self.SMTP_PASSWORD = smtp_pass
        return self

    @property
    def trusted_hosts_list(self) -> List[str]:
        hosts = [h.strip() for h in self.TRUSTED_HOSTS.split(",") if h.strip()]
        return hosts or ["localhost", "127.0.0.1"]


settings = Settings()
