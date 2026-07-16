import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_database_session
from app.models import User


load_dotenv()


JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )
)


if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is missing. "
        "Add it to backend/.env."
    )


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
    Verify a plain password against its hash.
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

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=(
                ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> int:
    """
    Decode a token and return the user ID.
    """

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        subject = payload.get("sub")

        if subject is None:
            raise ValueError(
                "Token subject is missing."
            )

        return int(subject)

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
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
    Find a user by normalized email.
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
    Validate login credentials.
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
    Return the authenticated user.
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
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
            status_code=status.HTTP_401_UNAUTHORIZED,
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "The authenticated user "
                "does not exist or is inactive."
            ),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return user