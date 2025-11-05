from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    OPENROUTER_API_KEY: str = "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"
    DATABASE_URL: str = "sqlite:///./borg.db"

    class Config:
        env_file = ".env"


settings = Settings()
