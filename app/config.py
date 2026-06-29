from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "KB Search"
    debug: bool = False

    # Database
    database_url: str = "postgresql://kb:kb@db:5432/kb"

    # Redis
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"

    # Security
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 30

    # File Storage
    upload_dir: str = "/tmp/uploads"
    max_upload_size: int = 20 * 1024 * 1024  # 20MB

    # Auth
    auth_type: str = "local"  # local | ldap | oauth2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
