from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    webapp_url: str
    api_url: str = "http://localhost:8000"

    database_url: str = ""
    database_url: str = ""
    database_path: str = "data/kupidon.db"
    upload_dir: str = "data/uploads"

    cors_origins: str = "http://localhost:5173"

    admin_ids: str = ""
    debug: bool = False
    dev_telegram_id: int = 0
    report_threshold: int = 3

    telegram_proxy: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def admin_id_set(self) -> set[int]:
        return {
            int(x.strip())
            for x in self.admin_ids.split(",")
            if x.strip().isdigit()
        }

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
