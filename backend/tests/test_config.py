from app.config import Settings


def test_default_settings() -> None:
    settings = Settings(
        jwt_secret_key=(
            "test-secret-key-that-is-"
            "longer-than-thirty-two-characters"
        ),
        _env_file=None,
    )

    assert settings.app_name == (
        "AI Resume Analyzer API"
    )

    assert (
        settings.app_environment
        == "development"
    )

    assert (
        settings.maximum_file_size_bytes
        == 5 * 1024 * 1024
    )

    assert (
        settings
        .semantic_model_local_only
        is True
    )


def test_comma_separated_cors_origins() -> None:
    settings = Settings(
        jwt_secret_key=(
            "test-secret-key-that-is-"
            "longer-than-thirty-two-characters"
        ),
        cors_origins=(
            "http://localhost:5173,"
            "http://127.0.0.1:5173"
        ),
        _env_file=None,
    )

    assert settings.cors_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_maximum_file_size_conversion() -> None:
    settings = Settings(
        jwt_secret_key=(
            "test-secret-key-that-is-"
            "longer-than-thirty-two-characters"
        ),
        maximum_file_size_mb=10,
        _env_file=None,
    )

    assert (
        settings.maximum_file_size_bytes
        == 10 * 1024 * 1024
    )


def test_environment_helpers() -> None:
    settings = Settings(
        jwt_secret_key=(
            "test-secret-key-that-is-"
            "longer-than-thirty-two-characters"
        ),
        app_environment="production",
        _env_file=None,
    )

    assert settings.is_production is True
    assert settings.is_development is False
    assert settings.is_testing is False