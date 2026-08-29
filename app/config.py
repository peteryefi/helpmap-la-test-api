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
    RATE_LIMIT_DELETE: str = "30/minute"

    # GET /reports only returns reports created within this many hours.
    # Hardcoded-but-tunable. Common values: 24 (1 day), 48 (2 days),
    # 96 (4 days), 168 (1 week).
    REPORT_WINDOW_HOURS: int = 24*30

    # Max length of the base64-encoded photo string (characters, not bytes
    # -- base64 runs ~33% larger than the underlying image). 8,000,000 chars
    # ≈ 6MB of image data
    MAX_PHOTO_BASE64_CHARS: int = 8_000_000

    # Shared secret gating DELETE /reports/{id}. Everything else on this API
    # is intentionally open (no auth -- see README), but a delete is
    # destructive and irreversible, so it gets one narrow exception: the
    # caller must send this exact value in an `X-Admin-Token` header.
    #
    # Empty by default on purpose -- this makes the endpoint fail CLOSED
    # (503, "not configured") rather than open if you forget to set it,
    # instead of silently accepting an empty token as valid. Generate a real
    # value with `openssl rand -hex 32` and set it via .env / the systemd
    # EnvironmentFile; never commit the real value.
    ADMIN_DELETE_TOKEN: str = ""

    @property
    def cors_origin_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
