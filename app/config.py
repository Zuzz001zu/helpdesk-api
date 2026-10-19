from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Helpdesk API"
    database_url: str = "postgresql+psycopg://helpdesk:helpdesk@localhost:5432/helpdesk"
    # When empty, write endpoints are open (handy for local development).
    api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
