from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)

from app.config import settings


def is_sqlite_database(
    database_url: str,
) -> bool:
    """
    Return whether the database URL uses SQLite.
    """

    return database_url.startswith(
        "sqlite"
    )


def is_postgresql_database(
    database_url: str,
) -> bool:
    """
    Return whether the database URL uses PostgreSQL.
    """

    return database_url.startswith(
        "postgresql"
    )


def get_engine_options(
    database_url: str,
) -> dict[str, Any]:
    """
    Return database-specific SQLAlchemy
    engine options.
    """

    options: dict[str, Any] = {
        "pool_pre_ping": True,
    }

    if is_sqlite_database(
        database_url
    ):
        options["connect_args"] = {
            "check_same_thread": False,
        }

    elif is_postgresql_database(
        database_url
    ):
        options.update(
            {
                "pool_size": (
                    settings.database_pool_size
                ),
                "max_overflow": (
                    settings
                    .database_max_overflow
                ),
                "pool_timeout": (
                    settings
                    .database_pool_timeout_seconds
                ),
                "pool_recycle": (
                    settings
                    .database_pool_recycle_seconds
                ),
            }
        )

    return options


def create_database_engine() -> Engine:
    """
    Create the configured SQLAlchemy engine.
    """

    database_url = (
        settings.sqlalchemy_database_url
    )

    return create_engine(
        database_url,
        **get_engine_options(
            database_url
        ),
    )


engine = create_database_engine()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    """

    pass


def get_database_session() -> (
    Generator[Session, None, None]
):
    """
    Create one database session per request.
    """

    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()


def create_database_tables() -> None:
    """
    Create database tables directly.

    This helper is intended only for isolated tests,
    development utilities, or emergency local setup.

    Application schema changes must be managed
    through Alembic migrations.
    """

    from app import models  # noqa: F401

    Base.metadata.create_all(
        bind=engine
    )