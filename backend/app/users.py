from sqlalchemy.orm import Session

from app.auth import (
    get_user_by_email,
    hash_password,
)
from app.models import User


def create_user(
    database_session: Session,
    *,
    name: str,
    email: str,
    password: str,
) -> User:
    """
    Create and persist a new user.
    """

    normalized_name = name.strip()
    normalized_email = (
        email.strip().lower()
    )

    existing_user = get_user_by_email(
        database_session,
        normalized_email,
    )

    if existing_user is not None:
        raise ValueError(
            "An account with this email "
            "already exists."
        )

    user = User(
        name=normalized_name,
        email=normalized_email,
        password_hash=hash_password(
            password
        ),
    )

    database_session.add(user)
    database_session.commit()
    database_session.refresh(user)

    return user