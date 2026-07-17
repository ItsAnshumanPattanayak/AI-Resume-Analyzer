from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_database_session
from app.main import app


@pytest.fixture
def auth_headers(
    client,
) -> dict[str, str]:
    """
    Register and log in a unique test user.
    """

    unique_email = (
        f"api-test-{uuid4().hex}@example.com"
    )

    password = "StrongPassword123"

    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "API Test User",
            "email": unique_email,
            "password": password,
        },
    )

    assert (
        register_response.status_code
        == 201
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": unique_email,
            "password": password,
        },
    )

    assert (
        login_response.status_code
        == 200
    )

    token = login_response.json()[
        "access_token"
    ]

    return {
        "Authorization": (
            f"Bearer {token}"
        ),
    }


def test_root_endpoint(
    client,
) -> None:
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == (
        "AI Resume Analyzer API is running."
    )

    assert "version" in data
    assert data["documentation"] == "/docs"


def test_health_endpoint(
    client,
) -> None:
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert (
        data["authentication"]
        == "enabled"
    )


def test_health_endpoint_reports_database_failure(client) -> None:
    class UnavailableDatabaseSession:
        def execute(self, statement):
            raise SQLAlchemyError("private database detail")

    def override_database_session():
        yield UnavailableDatabaseSession()

    app.dependency_overrides[get_database_session] = (
        override_database_session
    )

    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides.pop(get_database_session, None)

    assert response.status_code == 503
    assert "private database detail" not in response.text


def test_resume_endpoint_requires_authentication(
    client,
    simple_docx_bytes: bytes,
) -> None:
    """
    Protected resume endpoints should reject
    unauthenticated requests.
    """

    response = client.post(
        "/api/resume/parse",
        files={
            "file": (
                "resume.docx",
                simple_docx_bytes,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
            )
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["success"] is False

    assert (
        "authentication"
        in str(
            data["error"]["message"]
        ).lower()
    )


def test_parse_docx_endpoint(
    client,
    simple_docx_bytes: bytes,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/resume/parse",
        headers=auth_headers,
        files={
            "file": (
                "resume.docx",
                simple_docx_bytes,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert (
        data["filename"]
        == "resume.docx"
    )
    assert data["word_count"] > 0
    assert "parsed_data" in data
    assert "history_id" in data
    assert isinstance(
        data["history_id"],
        int,
    )


def test_reject_unsupported_file(
    client,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/resume/parse",
        headers=auth_headers,
        files={
            "file": (
                "resume.txt",
                b"Python developer",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415

    data = response.json()

    assert data["success"] is False
    assert (
        data["error"]["type"]
        == "http_error"
    )

    error_message = str(
        data["error"]["message"]
    ).lower()

    assert (
        "unsupported"
        in error_message
    )


def test_reject_empty_resume(
    client,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/resume/parse",
        headers=auth_headers,
        files={
            "file": (
                "resume.pdf",
                b"",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["success"] is False

    assert (
        "empty"
        in str(
            data["error"]["message"]
        ).lower()
    )


def test_reject_short_job_description(
    client,
    simple_docx_bytes: bytes,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/resume/analyze",
        headers=auth_headers,
        files={
            "file": (
                "resume.docx",
                simple_docx_bytes,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
            )
        },
        data={
            "job_description": (
                "Python developer"
            ),
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["success"] is False

    assert (
        "too short"
        in str(
            data["error"]["message"]
        ).lower()
    )


def test_improve_resume_endpoint(
    client,
    simple_docx_bytes: bytes,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/resume/improve",
        headers=auth_headers,
        files={
            "file": (
                "resume.docx",
                simple_docx_bytes,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "resume_improvement" in data
    assert "history_id" in data
    assert isinstance(
        data["history_id"],
        int,
    )


def test_history_contains_created_record(
    client,
    simple_docx_bytes: bytes,
    auth_headers: dict[str, str],
) -> None:
    parse_response = client.post(
        "/api/resume/parse",
        headers=auth_headers,
        files={
            "file": (
                "resume.docx",
                simple_docx_bytes,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
            )
        },
    )

    assert (
        parse_response.status_code
        == 200
    )

    history_id = (
        parse_response.json()[
            "history_id"
        ]
    )

    history_response = client.get(
        "/api/history",
        headers=auth_headers,
    )

    assert (
        history_response.status_code
        == 200
    )

    records = history_response.json()

    assert len(records) >= 1

    matching_records = [
        record
        for record in records
        if record["id"] == history_id
    ]

    assert len(matching_records) == 1

    assert (
        matching_records[0][
            "analysis_type"
        ]
        == "parse"
    )


def test_open_history_record(
    client,
    simple_docx_bytes: bytes,
    auth_headers: dict[str, str],
) -> None:
    parse_response = client.post(
        "/api/resume/parse",
        headers=auth_headers,
        files={
            "file": (
                "resume.docx",
                simple_docx_bytes,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
            )
        },
    )

    history_id = (
        parse_response.json()[
            "history_id"
        ]
    )

    response = client.get(
        f"/api/history/{history_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == history_id
    assert (
        data["analysis_type"]
        == "parse"
    )
    assert (
        data["filename"]
        == "resume.docx"
    )
    assert "result_data" in data


def test_delete_history_record(
    client,
    simple_docx_bytes: bytes,
    auth_headers: dict[str, str],
) -> None:
    parse_response = client.post(
        "/api/resume/parse",
        headers=auth_headers,
        files={
            "file": (
                "resume.docx",
                simple_docx_bytes,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
            )
        },
    )

    history_id = (
        parse_response.json()[
            "history_id"
        ]
    )

    delete_response = client.delete(
        f"/api/history/{history_id}",
        headers=auth_headers,
    )

    assert (
        delete_response.status_code
        == 200
    )

    assert delete_response.json() == {
        "success": True,
        "deleted_id": history_id,
    }

    get_response = client.get(
        f"/api/history/{history_id}",
        headers=auth_headers,
    )

    assert (
        get_response.status_code
        == 404
    )


def test_rejects_misleading_pdf_extension(
    client,
    auth_headers,
) -> None:
    response = client.post(
        "/api/resume/parse",
        headers=auth_headers,
        files={
            "file": (
                "resume.pdf",
                b"this is not a PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422
    assert "valid PDF" in response.text


def test_uploaded_filename_is_normalized(
    client,
    auth_headers,
    simple_docx_bytes: bytes,
) -> None:
    response = client.post(
        "/api/resume/parse",
        headers=auth_headers,
        files={
            "file": (
                "../../private/resume.docx",
                simple_docx_bytes,
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "resume.docx"
