"""Configuration is validated before the web server or worker starts."""

import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    provider: str = "live"
    database_path: Path = Path("data/travel.db")
    base_url: str = "http://127.0.0.1:8000"
    secret: str = ""
    serp_api_key: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    mail_from: str = ""
    daily_provider_limit: int = 500
    alert_interval: int = 43200

    @property
    def production(self):
        return self.environment == "production"

    def validate(self):
        if self.environment not in {"development", "production", "test"}:
            raise ValueError("APP_ENV must be development, production or test")
        if self.provider not in {"live", "demo"}:
            raise ValueError("FLIGHT_PROVIDER must be live or demo")
        parsed = urlsplit(self.base_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError("BASE_URL must contain only scheme, host and optional port")
        if self.production:
            checks = [
                self.provider == "live",
                len(self.secret) >= 32 and not self.secret.startswith("replace-"),
                parsed.scheme == "https",
                bool(self.serp_api_key),
                bool(self.smtp_host and self.mail_from),
            ]
            if not all(checks):
                raise ValueError(
                    "Production requires live flights, APP_SECRET (32+ chars), HTTPS BASE_URL, SERP_API_KEY, SMTP_HOST and MAIL_FROM"
                )
        if self.alert_interval < 3600 or self.daily_provider_limit < 1:
            raise ValueError("Alert interval must be >= 3600s and provider limit must be positive")
        return self

    @classmethod
    def from_env(cls):
        load_dotenv()
        return cls(
            environment=os.getenv("APP_ENV", "development"),
            provider=os.getenv("FLIGHT_PROVIDER", "live"),
            database_path=Path(os.getenv("DATABASE_PATH", "data/travel.db")),
            base_url=os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
            secret=os.getenv("APP_SECRET")
            or ("" if os.getenv("APP_ENV") == "production" else secrets.token_urlsafe(48)),
            serp_api_key=os.getenv("SERP_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            mail_from=os.getenv("MAIL_FROM", ""),
            daily_provider_limit=int(os.getenv("DAILY_PROVIDER_LIMIT", "500")),
            alert_interval=int(os.getenv("ALERT_INTERVAL_SECONDS", "43200")),
        ).validate()
