"""
App configuration, loaded from environment variables (never hardcoded).
Used by db/session.py now; auth/security.py (Part 2) will add JWT settings
here too (SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, etc.).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://ums_user:ums_password@localhost:5432/ums_db"

    # seeded single-university id for this build phase — used anywhere we
    # need a default university_id (e.g. seed scripts). Real requests will
    # always derive university_id from the authenticated user, never from
    # this constant, once Part 2 (auth) is in place.
    DEFAULT_UNIVERSITY_ID: int = 1

    # --- Auth / JWT settings ---
    # NEVER commit a real secret. This default is only here so the app
    # doesn't crash if .env is missing in local dev; production MUST set
    # JWT_SECRET_KEY via environment variable / secrets manager.
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_ENV_FILE"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # rate limit on /auth/login — "5/minute" means 5 requests per minute
    # per client IP, enforced by slowapi
    LOGIN_RATE_LIMIT: str = "5/minute"

    # attendance % below this triggers an automatic low-attendance
    # notification to the student (and, in a future part, their parent)
    LOW_ATTENDANCE_THRESHOLD_PERCENT: float = 75.0


settings = Settings()
