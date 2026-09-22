from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Broke-Proof API"
    api_prefix: str = "/api"
    secret_key: str = "change-me-in-production"
    access_token_minutes: int = 60
    refresh_token_days: int = 30
    database_url: str = "sqlite:///./brokeproof.db"
    cors_origins: str = "http://localhost:5173"
    llm_api_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    no_spend_weekend_daily_cap: float = 50.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
