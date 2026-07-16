from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import (
    Field,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Centralized application configuration.

    Values are loaded from environment variables
    and the backend/.env file.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = (
        "AI Resume Analyzer API"
    )

    app_version: str = "1.5.0"

    app_environment: Literal[
        "development",
        "testing",
        "production",
    ] = "development"

    debug: bool = False

    database_url: str = (
        f"sqlite:///"
        f"{(BASE_DIR / 'resume_analyzer.db').as_posix()}"
    )

    jwt_secret_key: str = Field(
        min_length=32,
    )

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
        le=10080,
    )

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    allow_localhost_origin_regex: bool = True

    maximum_file_size_mb: int = Field(
        default=5,
        ge=1,
        le=50,
    )

    semantic_model_name: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    semantic_model_local_only: bool = True

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    @field_validator(
        "cors_origins",
        mode="before",
    )
    @classmethod
    def parse_cors_origins(
        cls,
        value,
    ) -> list[str]:
        """
        Accept either:

        CORS_ORIGINS=["http://localhost:5173"]

        or:

        CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
        """

        if isinstance(value, str):
            cleaned_value = value.strip()

            if not cleaned_value:
                return []

            if cleaned_value.startswith("["):
                return value

            return [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]

        return value

    @property
    def maximum_file_size_bytes(
        self,
    ) -> int:
        """
        Convert configured megabytes to bytes.
        """

        return (
            self.maximum_file_size_mb
            * 1024
            * 1024
        )

    @property
    def is_development(self) -> bool:
        return (
            self.app_environment
            == "development"
        )

    @property
    def is_testing(self) -> bool:
        return (
            self.app_environment
            == "testing"
        )

    @property
    def is_production(self) -> bool:
        return (
            self.app_environment
            == "production"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load and cache application settings.
    """

    return Settings()


settings = get_settings()