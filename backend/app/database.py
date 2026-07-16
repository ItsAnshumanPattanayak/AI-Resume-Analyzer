from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "resume_analyzer.db"

DATABASE_URL = f"sqlite:///{DATABASE_FILE.as_posix()}"


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy database models.
    """

    pass


def get_database_session() -> Generator[Session, None, None]:
    """
    Create one database session for a request
    and close it after the request finishes.
    """

    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()


def create_database_tables() -> None:
    """
    Create any database tables that do not exist.
    """

    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)