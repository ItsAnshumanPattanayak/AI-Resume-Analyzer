import pytest
from pydantic import ValidationError

from app.config import Settings


TEST_SECRET_KEY = (
    "test-secret-key-that-is-"
    "longer-than-thirty-two-characters"
)


def create_test_settings(
    **overrides,
) -> Settings:
    """
    Create isolated settings without reading .env.
    """

    values = {
        "jwt_secret_key": (
            TEST_SECRET_KEY
        ),
        "app_name": (
            "AI Resume Analyzer API"
        ),
        "app_version": "1.5.0",
        "app_environment": (
            "development"
        ),
        "debug": False,
        "database_url": (
            "sqlite:///test.db"
        ),
        "maximum_file_size_mb": 5,
        "semantic_model_local_only": True,
        "cors_origins": [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
    }

    values.update(overrides)

    return Settings(
        **values,
        _env_file=None,
    )


def test_default_settings() -> None:
    test_settings = (
        create_test_settings()
    )

    assert test_settings.app_name == (
        "AI Resume Analyzer API"
    )

    assert (
        test_settings.app_environment
        == "development"
    )

    assert (
        test_settings
        .maximum_file_size_bytes
        == 5 * 1024 * 1024
    )

    assert (
        test_settings
        .semantic_model_local_only
        is True
    )

    assert (
        test_settings
        .database_pool_size
        == 5
    )

    assert (
        test_settings
        .database_max_overflow
        == 10
    )


def test_comma_separated_cors_origins() -> None:
    test_settings = (
        create_test_settings(
            cors_origins=(
                "http://localhost:5173,"
                "http://127.0.0.1:5173"
            )
        )
    )

    assert test_settings.cors_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_json_cors_origins() -> None:
    test_settings = (
        create_test_settings(
            cors_origins=(
                '["http://localhost:5173",'
                '"https://example.com"]'
            )
        )
    )

    assert test_settings.cors_origins == [
        "http://localhost:5173",
        "https://example.com",
    ]


def test_cors_origins_remove_duplicates() -> None:
    test_settings = (
        create_test_settings(
            cors_origins=[
                "http://localhost:5173",
                "http://localhost:5173/",
                "https://example.com",
            ]
        )
    )

    assert test_settings.cors_origins == [
        "http://localhost:5173",
        "https://example.com",
    ]


def test_invalid_cors_origin_is_rejected() -> None:
    with pytest.raises(
        ValidationError
    ):
        create_test_settings(
            cors_origins=[
                "localhost:5173",
            ]
        )


def test_maximum_file_size_conversion() -> None:
    test_settings = (
        create_test_settings(
            maximum_file_size_mb=10
        )
    )

    assert (
        test_settings
        .maximum_file_size_bytes
        == 10 * 1024 * 1024
    )


def test_environment_helpers() -> None:
    test_settings = (
        create_test_settings(
            app_environment="production"
        )
    )

    assert (
        test_settings.is_production
        is True
    )

    assert (
        test_settings.is_development
        is False
    )

    assert (
        test_settings.is_testing
        is False
    )


def test_sqlite_database_url_is_unchanged() -> None:
    test_settings = (
        create_test_settings(
            database_url=(
                "sqlite:///test.db"
            )
        )
    )

    assert (
        test_settings
        .sqlalchemy_database_url
        == "sqlite:///test.db"
    )

    assert (
        test_settings.is_sqlite_database
        is True
    )

    assert (
        test_settings
        .is_postgresql_database
        is False
    )


def test_postgres_url_is_normalized() -> None:
    test_settings = (
        create_test_settings(
            database_url=(
                "postgres://"
                "user:password"
                "@localhost:5432/database"
            )
        )
    )

    assert (
        test_settings
        .sqlalchemy_database_url
        == (
            "postgresql+psycopg://"
            "user:password"
            "@localhost:5432/database"
        )
    )


def test_postgresql_url_is_normalized() -> None:
    test_settings = (
        create_test_settings(
            database_url=(
                "postgresql://"
                "user:password"
                "@localhost:5432/database"
            )
        )
    )

    assert (
        test_settings
        .sqlalchemy_database_url
        == (
            "postgresql+psycopg://"
            "user:password"
            "@localhost:5432/database"
        )
    )

    assert (
        test_settings
        .is_postgresql_database
        is True
    )


def test_psycopg_url_is_not_modified() -> None:
    database_url = (
        "postgresql+psycopg://"
        "user:password"
        "@localhost:5432/database"
    )

    test_settings = (
        create_test_settings(
            database_url=database_url
        )
    )

    assert (
        test_settings
        .sqlalchemy_database_url
        == database_url
    )


def test_empty_database_url_is_rejected() -> None:
    with pytest.raises(
        ValidationError
    ):
        create_test_settings(
            database_url=" "
        )


def test_unsupported_database_url_is_rejected() -> None:
    with pytest.raises(
        ValidationError
    ):
        create_test_settings(
            database_url=(
                "mysql://user:password"
                "@localhost/database"
            )
        )


def test_database_pool_settings() -> None:
    test_settings = (
        create_test_settings(
            database_pool_size=8,
            database_max_overflow=16,
            database_pool_timeout_seconds=45,
            database_pool_recycle_seconds=3600,
        )
    )

    assert (
        test_settings.database_pool_size
        == 8
    )

    assert (
        test_settings
        .database_max_overflow
        == 16
    )

    assert (
        test_settings
        .database_pool_timeout_seconds
        == 45
    )

    assert (
        test_settings
        .database_pool_recycle_seconds
        == 3600
    )


def test_rate_limit_defaults() -> None:
    test_settings = create_test_settings(
        rate_limit_enabled=True
    )

    assert Settings.model_fields[
        "rate_limit_enabled"
    ].default is True
    assert test_settings.rate_limit_enabled is True
    assert test_settings.rate_limit_window_seconds == 60
    assert test_settings.rate_limit_registration_requests == 5
    assert test_settings.rate_limit_login_requests == 10
    assert test_settings.rate_limit_resume_requests == 10


def test_performance_configuration_defaults_and_bounds() -> None:
    test_settings = create_test_settings()

    assert test_settings.semantic_result_cache_size == 32
    assert test_settings.performance_logging_enabled is False

    with pytest.raises(ValidationError):
        create_test_settings(semantic_result_cache_size=-1)


def test_unsupported_jwt_algorithm_is_rejected() -> None:
    with pytest.raises(ValidationError):
        create_test_settings(jwt_algorithm="none")
