from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Shared secret for the server-to-server subscription webhook.
    # Must match MLM_WEBHOOK_SECRET in the winwinlaw backend .env.
    MLM_WEBHOOK_SECRET: str = "change-this-shared-secret"

    # WWL internal sync — MLM calls this to register/deactivate referral codes.
    # WWL_INTERNAL_URL must point to the winwinlaw backend (e.g. http://winwinlaw-backend:8000).
    # WWL_SYNC_SECRET must match MLM_SYNC_SECRET in the winwinlaw backend .env.
    WWL_INTERNAL_URL: str = "http://localhost:8000"
    WWL_SYNC_SECRET: str = "change-this-sync-secret"

    # Frontend URL added to CORS allow-list. Set per-environment in Railway.
    FRONTEND_URL: str = "http://localhost:5173"

    # SMTP — used for invite emails. Leave blank to skip sending (token is logged instead).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@winwinlaw.com"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
