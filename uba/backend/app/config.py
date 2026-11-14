"""All configuration comes from environment variables (12-factor style).

Nothing in the code knows whether it is running on a laptop, in Docker or in
the cloud. Docker Compose sets these variables; see docker-compose.yml.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="UBA_", env_file=".env", extra="ignore")

    environment: str = "development"

    # SQLite by default so the tests and a bare `uvicorn` run need no setup.
    # In Docker this is overridden with a PostgreSQL URL.
    database_url: str = "sqlite:///./uba.db"

    # Used to sign login tokens. MUST be replaced with a long random value.
    jwt_secret: str = "change-me-in-production-with-a-long-random-value"
    jwt_expire_minutes: int = 60
    cookie_name: str = "uba_session"
    cookie_secure: bool = False  # True once the site is served over HTTPS

    # Where password-reset emails are sent, and the address used in links.
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    mail_from: str = "no-reply@example.com"
    public_url: str = "http://localhost"
    reset_token_minutes: int = 30

    seed_demo_data: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
