from app.database import (
    get_engine_options,
    is_postgresql_database,
    is_sqlite_database,
)


def test_identifies_sqlite_database() -> None:
    database_url = "sqlite:///test.db"

    assert (
        is_sqlite_database(
            database_url
        )
        is True
    )

    assert (
        is_postgresql_database(
            database_url
        )
        is False
    )


def test_identifies_postgresql_database() -> None:
    database_url = (
        "postgresql+psycopg://"
        "user:password"
        "@localhost:5432/database"
    )

    assert (
        is_postgresql_database(
            database_url
        )
        is True
    )

    assert (
        is_sqlite_database(
            database_url
        )
        is False
    )


def test_sqlite_engine_options() -> None:
    options = get_engine_options(
        "sqlite:///test.db"
    )

    assert (
        options["pool_pre_ping"]
        is True
    )

    assert options["connect_args"] == {
        "check_same_thread": False,
    }

    assert "pool_size" not in options
    assert "max_overflow" not in options


def test_postgresql_engine_options() -> None:
    options = get_engine_options(
        (
            "postgresql+psycopg://"
            "user:password"
            "@localhost:5432/database"
        )
    )

    assert (
        options["pool_pre_ping"]
        is True
    )

    assert options["pool_size"] >= 1
    assert options["max_overflow"] >= 0
    assert options["pool_timeout"] >= 1
    assert options["pool_recycle"] >= 60

    assert "connect_args" not in options