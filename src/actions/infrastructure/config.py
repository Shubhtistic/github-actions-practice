from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- Common ---
class CommonSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# --- Postgres ---
class PostgresSettings(CommonSettings):

    postgres_server: str = Field(validation_alias="POSTGRES_SERVER")

    postgres_port: int = Field(validation_alias="POSTGRES_PORT")

    postgres_user: str = Field(validation_alias="POSTGRES_USER")

    postgres_password: str = Field(validation_alias="POSTGRES_PASSWORD")

    postgres_db: str = Field(validation_alias="POSTGRES_DB")

    @property
    def postgres_async_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}:"
            f"{self.postgres_password}"
            f"@{self.postgres_server}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )


# --- App settings ---
class AppSettings(CommonSettings):

    environment: str = Field(validation_alias="ENVIRONMENT")

    project_name: str = Field(validation_alias="PROJECT_NAME")

    version: str = Field(validation_alias="VERSION")


# --- Main Settings ---
class Settings(CommonSettings):

    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    app: AppSettings = Field(default_factory=AppSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
