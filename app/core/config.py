from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn

class Settings(BaseSettings):
    APP_NAME: str = "IMAGE EHR"
    SECRET_KEY: str
    SESSION_TIMEOUT_MIN: int = 30
    POSTGRES_DSN: PostgresDsn

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()