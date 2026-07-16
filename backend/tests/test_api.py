def test_root_endpoint(client) -> None:
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == (
        "AI Resume Analyzer API is running."
    )


def test_health_endpoint(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_parse_docx_endpoint(
    client,
    simple_docx_bytes: bytes,
) -> None:
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

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["filename"] == "resume.docx"
    assert data["word_count"] > 0
    assert "parsed_data" in data


def test_reject_unsupported_file(
    client,
) -> None:
    response = client.post(
        "/api/resume/parse",
        files={
            "file": (
                "resume.txt",
                b"Python developer",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415


def test_reject_empty_resume(
    client,
) -> None:
    response = client.post(
        "/api/resume/parse",
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
    assert "empty" in str(
        data["error"]["message"]
    ).lower()


def test_reject_short_job_description(
    client,
    simple_docx_bytes: bytes,
) -> None:
    response = client.post(
        "/api/resume/analyze",
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
            "job_description": "Python developer",
        },
    )

    assert response.status_code == 400


def test_improve_resume_endpoint(
    client,
    simple_docx_bytes: bytes,
) -> None:
    response = client.post(
        "/api/resume/improve",
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

def test_reject_unsupported_file(
    client,
) -> None:
    response = client.post(
        "/api/resume/parse",
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
    assert data["error"]["type"] == (
        "http_error"
    )