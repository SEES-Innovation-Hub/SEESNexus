"""
Centralized configuration, loaded from environment variables.
See .env.example at the repo root for the full list of variables (Tech Doc §9.1).
"""
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    # Production/staging should point this at Postgres, e.g.:
    #   postgresql+asyncpg://user:pass@host/db
    # Local dev without Docker falls back to a file-based SQLite DB so the
    # app is runnable out of the box; docker-compose.yml wires up real
    # Postgres per Tech Doc §9.2.
    DATABASE_URL: str = "sqlite+aiosqlite:///./sees_nexus.db"

    # --- Auth / JWT ---
    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Cloudinary (image upload — used by /upload, not part of this slice) ---
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # --- Brevo (OTP / transactional email) ---
    BREVO_API_KEY: str = ""
    BREVO_SENDER_EMAIL: str = "noreply@seesnexus.example"
    BREVO_SENDER_NAME: str = "SEES Nexus"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173"

    # --- OTP behavior ---
    OTP_EXPIRE_MINUTES: int = 10
    # When true, /notify/send-code returns the generated code in the response
    # body so it can be used without a real email provider (dev/test only).
    OTP_DEBUG_RETURN_CODE: bool = True

    @field_validator("DATABASE_URL")
    @classmethod
    def _use_async_driver(cls, value: str) -> str:
        # Render, Heroku and most managed Postgres hosts hand out
        # "postgres://..." or "postgresql://...", which SQLAlchemy would open
        # with a sync driver the async engine can't use.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+asyncpg://" + value[len(prefix):]
        return value

    @model_validator(mode="after")
    def _refuse_default_secret_outside_sqlite(self) -> "Settings":
        # Every JWT is signed with SECRET_KEY: with the public default, anyone
        # could mint an admin token. Local SQLite dev may keep it; a real
        # database may not.
        placeholder = self.SECRET_KEY == DEFAULT_SECRET_KEY or self.SECRET_KEY.startswith("change-me")
        if placeholder and not self.is_sqlite:
            raise ValueError("SECRET_KEY must be set to a private value when using a real database")
        return self

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
