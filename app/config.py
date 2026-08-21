"""Application settings, loaded from environment variables / a .env file."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"

    # SQLite file on local disk.
    DATABASE_URL: str = "sqlite:///./data/reports.db"

    # Comma-separated list, e.g. "https://main.xxxxxxxxx.amplifyapp.com".
    # Defaults to "*" for testbed convenience -- there is no auth on this API
    CORS_ORIGINS: str = "*"

    # Rate limits, in the slowapi/`limits` mini-language ("N/period").
    RATE_LIMIT_SUBMIT: str = "15/minute"
    RATE_LIMIT_LIST: str = "60/minute"

    # GET /reports only returns reports created within this many hours.
    # Hardcoded-but-tunable. Common values: 24 (1 day), 48 (2 days),
    # 96 (4 days), 168 (1 week).
    REPORT_WINDOW_HOURS: int = 24

    # Max length of the base64-encoded photo string (characters, not bytes
    # -- base64 runs ~33% larger than the underlying image). 8,000,000 chars
    # ≈ 6MB of image data
    MAX_PHOTO_BASE64_CHARS: int = 8_000_000

    @property
    def cors_origin_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
