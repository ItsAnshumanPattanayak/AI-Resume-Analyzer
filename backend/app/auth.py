from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_database_session
from app.models import User


password_hash = PasswordHash.recommended()

bearer_scheme = HTTPBearer(
    auto_error=False,
)


def hash_password(
    password: str,
) -> str:
    """
    Hash a plain-text password securely.
    """

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    stored_password_hash: str,
) -> bool:
    """
    Verify a plain password against its stored hash.
    """

    return password_hash.verify(
        plain_password,
        stored_password_hash,
    )


def create_access_token(
    user_id: int,
) -> str:
    """
    Create a signed JWT access token.
    """

    issued_at = datetime.now(
        timezone.utc
    )

    expires_at = (
        issued_at
        + timedelta(
            minutes=(
                settings
                .access_token_expire_minutes
            )
        )
    )

    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=(
            settings.jwt_algorithm
        ),
    )


def decode_access_token(
    token: str,
) -> int:
    """
    Decode a JWT and return its user ID.
    """

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[
                settings.jwt_algorithm
            ],
        )

        subject = payload.get("sub")

        if subject is None:
            raise ValueError(
                "Token subject is missing."
            )

        user_id = int(subject)

        if user_id <= 0:
            raise ValueError(
                "Token subject is invalid."
            )

        return user_id

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid or expired access token."
            ),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from error


def get_user_by_email(
    database_session: Session,
    email: str,
) -> User | None:
    """
    Find a user by normalized email address.
    """

    normalized_email = (
        email.strip().lower()
    )

    statement = select(User).where(
        User.email == normalized_email
    )

    return database_session.scalar(
        statement
    )


def authenticate_user(
    database_session: Session,
    *,
    email: str,
    password: str,
) -> User | None:
    """
    Validate a user's login credentials.
    """

    user = get_user_by_email(
        database_session,
        email,
    )

    if user is None:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    if not user.is_active:
        return None

    return user


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    database_session: Annotated[
        Session,
        Depends(get_database_session),
    ],
) -> User:
    """
    Return the currently authenticated user.
    """

    if credentials is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Authentication is required."
            ),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if (
        credentials.scheme.lower()
        != "bearer"
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid authentication scheme."
            ),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    user_id = decode_access_token(
        credentials.credentials
    )

    user = database_session.get(
        User,
        user_id,
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "The authenticated user does not "
                "exist or is inactive."
            ),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return user