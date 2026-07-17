import json
from functools import lru_cache
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Literal,
)

from pydantic import (
    Field,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    NoDecode,
    SettingsConfigDict,
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


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
        "sqlite:///"
        f"{(
            BASE_DIR
            / 'resume_analyzer.db'
        ).as_posix()}"
    )

    database_pool_size: int = Field(
        default=5,
        ge=1,
        le=50,
    )

    database_max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
    )

    database_pool_timeout_seconds: int = (
        Field(
            default=30,
            ge=1,
            le=300,
        )
    )

    database_pool_recycle_seconds: int = (
        Field(
            default=1800,
            ge=60,
            le=86400,
        )
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

    cors_origins: Annotated[
        list[str],
        NoDecode,
    ] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    allow_localhost_origin_regex: bool = True

    maximum_file_size_mb: int = Field(
        default=5,
        ge=1,
        le=50,
    )

    semantic_model_name: str = (
        "sentence-transformers/"
        "all-MiniLM-L6-v2"
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
        "database_url",
        mode="before",
    )
    @classmethod
    def validate_database_url(
        cls,
        value: Any,
    ) -> str:
        """
        Validate and clean the configured database URL.
        """

        if not isinstance(value, str):
            raise ValueError(
                "DATABASE_URL must be a string."
            )

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "DATABASE_URL cannot be empty."
            )

        supported_prefixes = (
            "sqlite://",
            "postgres://",
            "postgresql://",
            "postgresql+psycopg://",
        )

        if not cleaned_value.startswith(
            supported_prefixes
        ):
            raise ValueError(
                "DATABASE_URL must use SQLite "
                "or PostgreSQL."
            )

        return cleaned_value

    @field_validator(
        "cors_origins",
        mode="before",
    )
    @classmethod
    def parse_cors_origins(
        cls,
        value: Any,
    ) -> list[str]:
        """
        Accept CORS origins as either:

        CORS_ORIGINS=[
            "http://localhost:5173"
        ]

        or:

        CORS_ORIGINS=http://localhost:5173,
        http://127.0.0.1:5173
        """

        if value is None:
            return []

        if isinstance(value, str):
            cleaned_value = value.strip()

            if not cleaned_value:
                return []

            if cleaned_value.startswith("["):
                try:
                    parsed_value = json.loads(
                        cleaned_value
                    )
                except json.JSONDecodeError as error:
                    raise ValueError(
                        "CORS_ORIGINS contains "
                        "invalid JSON."
                    ) from error

                if not isinstance(
                    parsed_value,
                    list,
                ):
                    raise ValueError(
                        "CORS_ORIGINS JSON value "
                        "must be a list."
                    )

                value = parsed_value

            else:
                value = [
                    origin.strip()
                    for origin
                    in cleaned_value.split(",")
                    if origin.strip()
                ]

        if not isinstance(value, list):
            raise ValueError(
                "CORS_ORIGINS must be a list "
                "or comma-separated string."
            )

        cleaned_origins: list[str] = []

        for origin in value:
            if not isinstance(origin, str):
                raise ValueError(
                    "Every CORS origin must "
                    "be a string."
                )

            cleaned_origin = (
                origin.strip().rstrip("/")
            )

            if not cleaned_origin:
                continue

            if not cleaned_origin.startswith(
                (
                    "http://",
                    "https://",
                )
            ):
                raise ValueError(
                    "Every CORS origin must begin "
                    "with http:// or https://."
                )

            if (
                cleaned_origin
                not in cleaned_origins
            ):
                cleaned_origins.append(
                    cleaned_origin
                )

        return cleaned_origins

    @property
    def sqlalchemy_database_url(
        self,
    ) -> str:
        """
        Return a SQLAlchemy-compatible database URL.

        PostgreSQL URLs supplied by hosting providers
        are normalized to use the Psycopg 3 driver.
        """

        database_url = (
            self.database_url.strip()
        )

        if database_url.startswith(
            "postgres://"
        ):
            return database_url.replace(
                "postgres://",
                "postgresql+psycopg://",
                1,
            )

        if database_url.startswith(
            "postgresql://"
        ):
            return database_url.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )

        return database_url

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
    def is_sqlite_database(
        self,
    ) -> bool:
        """
        Return whether SQLite is configured.
        """

        return (
            self.sqlalchemy_database_url
            .startswith("sqlite")
        )

    @property
    def is_postgresql_database(
        self,
    ) -> bool:
        """
        Return whether PostgreSQL is configured.
        """

        return (
            self.sqlalchemy_database_url
            .startswith("postgresql")
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