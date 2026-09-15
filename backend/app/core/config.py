"""
Centralized configuration, loaded from environment variables.
See .env.example at the repo root for the full list of variables (Tech Doc §9.1).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    SECRET_KEY: str = "dev-secret-change-me"
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

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
