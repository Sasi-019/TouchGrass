"""Central, validated application configuration.

Every environment variable the backend reads is declared here so that a
missing or unsafe value fails *at startup* with one clear message, rather than
as a confusing error in the middle of a request.

No secrets live in this file. Real values belong in ``backend/.env`` (which is
git-ignored) or in your hosting provider's environment settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load backend/.env if it exists. Real environment variables always win.
load_dotenv(BASE_DIR / ".env")


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or unsafe."""


# Values people commonly leave in from copied examples. Refuse to run with them.
_PLACEHOLDER_SECRETS = {
    "",
    "change-me",
    "changeme",
    "secret",
    "your-secret",
    "your_jwt_secret",
    "replace-with-a-long-random-string",
}

DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(value: str | None, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


def normalize_database_url(url: str) -> str:
    """Hosting providers often hand out ``postgres://`` URLs.

    SQLAlchemy 1.4+ only understands ``postgresql://``.
    """
    url = (url or "").strip()
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str
    sql_echo: bool

    jwt_secret: str
    jwt_algorithm: str
    access_token_expire_minutes: int

    groq_api_key: str
    groq_model: str
    whisper_model: str
    max_audio_mb: int

    cors_origins: list[str]
    cors_origin_regex: str | None

    overpass_urls: list[str]
    nominatim_url: str
    http_user_agent: str

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


def load_settings(env: dict | None = None) -> Settings:
    """Build Settings from ``env`` (defaults to ``os.environ``)."""
    e = os.environ if env is None else env

    return Settings(
        environment=(e.get("APP_ENV") or "development").strip().lower(),
        database_url=normalize_database_url(e.get("DATABASE_URL") or ""),
        sql_echo=_bool(e.get("SQL_ECHO"), False),
        jwt_secret=(e.get("JWT_SECRET") or "").strip(),
        jwt_algorithm=(e.get("JWT_ALGORITHM") or "HS256").strip(),
        # A full day by default: a 30-minute token logs people out mid-activity.
        access_token_expire_minutes=_int(
            e.get("ACCESS_TOKEN_EXPIRE_MINUTES"), 1440
        ),
        groq_api_key=(e.get("GROQ_API_KEY") or "").strip(),
        groq_model=(e.get("GROQ_MODEL") or "openai/gpt-oss-20b").strip(),
        whisper_model=(
            e.get("WHISPER_MODEL") or "whisper-large-v3-turbo"
        ).strip(),
        max_audio_mb=_int(e.get("MAX_AUDIO_MB"), 20),
        cors_origins=_csv(e.get("CORS_ORIGINS") or DEFAULT_CORS_ORIGINS),
        cors_origin_regex=(e.get("CORS_ORIGIN_REGEX") or "").strip() or None,
        overpass_urls=_csv(
            e.get("OVERPASS_URLS")
            or "https://overpass-api.de/api/interpreter,"
            "https://overpass.kumi.systems/api/interpreter"
        ),
        nominatim_url=(
            e.get("NOMINATIM_URL")
            or "https://nominatim.openstreetmap.org/search"
        ).strip(),
        http_user_agent=(
            e.get("HTTP_USER_AGENT")
            or "TouchGrass/1.0 (open-source offline activity agent)"
        ).strip(),
    )


def find_problems(settings: Settings) -> list[str]:
    """Return a human-readable list of everything wrong with the config."""
    problems: list[str] = []

    if not settings.database_url:
        problems.append(
            "DATABASE_URL is not set "
            "(e.g. postgresql://user:password@localhost:5432/touchgrass)."
        )

    if settings.jwt_secret.lower() in _PLACEHOLDER_SECRETS:
        problems.append(
            "JWT_SECRET is not set (or is a placeholder). Generate one with: "
            "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    elif len(settings.jwt_secret) < 32 and settings.is_production:
        problems.append(
            "JWT_SECRET must be at least 32 characters in production."
        )

    if not settings.groq_api_key:
        problems.append(
            "GROQ_API_KEY is not set. Create a key at https://console.groq.com/keys."
        )

    if settings.access_token_expire_minutes <= 0:
        problems.append("ACCESS_TOKEN_EXPIRE_MINUTES must be a positive number.")

    if settings.is_production and "*" in settings.cors_origins:
        problems.append(
            "CORS_ORIGINS must list your real frontend URL(s) in production, not '*'."
        )

    return problems


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


def reload_settings() -> Settings:
    """Re-read the environment (used by tests)."""
    get_settings.cache_clear()
    return get_settings()


def require_valid_settings() -> Settings:
    """Return Settings or raise one ConfigError that lists *all* problems."""
    settings = get_settings()
    problems = find_problems(settings)

    if problems:
        bullet_list = "\n".join(f"  - {p}" for p in problems)
        raise ConfigError(
            "TouchGrass cannot start because of configuration problems:\n"
            f"{bullet_list}\n\n"
            "Copy backend/.env.example to backend/.env and fill in the values."
        )

    return settings
