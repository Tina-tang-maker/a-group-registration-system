from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str
    environment: str = "local"
    secret_key: str
    ai_provider: str = "openai_compatible"
    ai_api_key: str | None = None
    ai_base_url: str | None = None
    ai_model: str = "gpt-3.5-turbo"

    @property
    def is_local(self) -> bool:
        return self.environment in ("local", "test")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
