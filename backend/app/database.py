from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)

from app.config import settings


def get_engine_options() -> dict:
    """
    Return database-specific SQLAlchemy options.
    """

    options: dict = {
        "pool_pre_ping": True,
    }

    if settings.database_url.startswith(
        "sqlite"
    ):
        options["connect_args"] = {
            "check_same_thread": False,
        }

    return options


engine = create_engine(
    settings.database_url,
    **get_engine_options(),
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Base class for database models.
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
    Create missing database tables.

    Alembic will replace this behavior
    for production migrations later.
    """

    from app import models  # noqa: F401

    Base.metadata.create_all(
        bind=engine
    )