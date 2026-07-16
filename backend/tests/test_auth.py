from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import (
    Base,
    get_database_session,
)
from app.history import create_analysis_record
from app.main import app
from app.models import User


@pytest.fixture
def database_session() -> Generator[
    Session,
    None,
    None,
]:
    """
    Create a fresh in-memory database for each test.
    """

    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(
    database_session: Session,
) -> Generator[TestClient, None, None]:
    """
    Override the application database dependency.
    """

    def override_database_session():
        yield database_session

    app.dependency_overrides[
        get_database_session
    ] = override_database_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def register_user(
    client: TestClient,
    *,
    name: str = "Test User",
    email: str = "test@example.com",
    password: str = "StrongPassword123",
):
    return client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
        },
    )


def login_user(
    client: TestClient,
    *,
    email: str = "test@example.com",
    password: str = "StrongPassword123",
):
    return client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def authorization_header(
    token: str,
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def test_register_user(
    client: TestClient,
) -> None:
    response = register_user(client)

    assert response.status_code == 201

    body = response.json()

    assert body["name"] == "Test User"
    assert body["email"] == "test@example.com"
    assert body["is_active"] is True
    assert "password" not in body
    assert "password_hash" not in body


def test_duplicate_email_is_rejected(
    client: TestClient,
) -> None:
    first_response = register_user(client)
    second_response = register_user(client)

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    body = second_response.json()

    error_text = str(body).lower()

    assert "already exists" in error_text


def test_login_returns_access_token(
    client: TestClient,
) -> None:
    register_user(client)

    response = login_user(client)

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0
    assert body["user"]["email"] == (
        "test@example.com"
    )


def test_invalid_password_is_rejected(
    client: TestClient,
) -> None:
    register_user(client)

    response = login_user(
        client,
        password="WrongPassword123",
    )

    assert response.status_code == 401


def test_current_user_requires_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/auth/me"
    )

    assert response.status_code == 401


def test_current_user_with_valid_token(
    client: TestClient,
) -> None:
    register_user(client)

    login_response = login_user(client)
    token = login_response.json()[
        "access_token"
    ]

    response = client.get(
        "/api/auth/me",
        headers=authorization_header(token),
    )

    assert response.status_code == 200
    assert response.json()["email"] == (
        "test@example.com"
    )


def test_history_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/history"
    )

    assert response.status_code == 401


def test_users_only_see_their_own_history(
    client: TestClient,
    database_session: Session,
) -> None:
    register_user(
        client,
        name="First User",
        email="first@example.com",
    )

    register_user(
        client,
        name="Second User",
        email="second@example.com",
    )

    first_login = login_user(
        client,
        email="first@example.com",
    )

    second_login = login_user(
        client,
        email="second@example.com",
    )

    first_token = first_login.json()[
        "access_token"
    ]

    second_token = second_login.json()[
        "access_token"
    ]

    first_user = (
        database_session.query(User)
        .filter(
            User.email
            == "first@example.com"
        )
        .one()
    )

    record = create_analysis_record(
        database_session,
        user_id=first_user.id,
        analysis_type="parse",
        filename="private-resume.pdf",
        result_data={
            "success": True,
            "filename": (
                "private-resume.pdf"
            ),
            "parsed_data": {
                "name": "Private Candidate",
            },
        },
    )

    first_history = client.get(
        "/api/history",
        headers=authorization_header(
            first_token
        ),
    )

    second_history = client.get(
        "/api/history",
        headers=authorization_header(
            second_token
        ),
    )

    assert first_history.status_code == 200
    assert len(first_history.json()) == 1

    assert second_history.status_code == 200
    assert second_history.json() == []

    forbidden_open = client.get(
        f"/api/history/{record.id}",
        headers=authorization_header(
            second_token
        ),
    )

    assert forbidden_open.status_code == 404

    permitted_open = client.get(
        f"/api/history/{record.id}",
        headers=authorization_header(
            first_token
        ),
    )

    assert permitted_open.status_code == 200
    assert permitted_open.json()[
        "filename"
    ] == "private-resume.pdf"


def test_user_cannot_delete_another_users_record(
    client: TestClient,
    database_session: Session,
) -> None:
    register_user(
        client,
        name="Owner",
        email="owner@example.com",
    )

    register_user(
        client,
        name="Other User",
        email="other@example.com",
    )

    owner_token = login_user(
        client,
        email="owner@example.com",
    ).json()["access_token"]

    other_token = login_user(
        client,
        email="other@example.com",
    ).json()["access_token"]

    owner = (
        database_session.query(User)
        .filter(
            User.email
            == "owner@example.com"
        )
        .one()
    )

    record = create_analysis_record(
        database_session,
        user_id=owner.id,
        analysis_type="improve",
        filename="owner-resume.docx",
        result_data={
            "success": True,
            "filename": "owner-resume.docx",
        },
    )

    unauthorized_delete = client.delete(
        f"/api/history/{record.id}",
        headers=authorization_header(
            other_token
        ),
    )

    assert (
        unauthorized_delete.status_code
        == 404
    )

    authorized_delete = client.delete(
        f"/api/history/{record.id}",
        headers=authorization_header(
            owner_token
        ),
    )

    assert authorized_delete.status_code == 200
    assert authorized_delete.json() == {
        "success": True,
        "deleted_id": record.id,
    }