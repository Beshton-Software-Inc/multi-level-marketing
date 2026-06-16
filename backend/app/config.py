from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Shared secret for the server-to-server subscription webhook.
    # Must match MLM_WEBHOOK_SECRET in the winwinlaw backend .env.
    MLM_WEBHOOK_SECRET: str = "change-this-shared-secret"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
