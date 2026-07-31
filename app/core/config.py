"""
Application configuration.

We load settings from environment variables (via a .env file in development).
This is the standard 12-factor app approach: never hardcode secrets or
environment-specific values (DB URLs, secret keys) directly in code.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "NutriTrack AI"
    ENVIRONMENT: str = "development"

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./nutritrack.db"

    # --- Auth / JWT ---
    SECRET_KEY: str  # required, no default — must come from .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    class Config:
        env_file = ".env"


# A single shared instance, imported everywhere else that needs config.
# This avoids re-reading environment variables all over the codebase.
settings = Settings()
