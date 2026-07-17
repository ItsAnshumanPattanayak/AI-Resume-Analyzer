"""Opt-in smoke checks for an already deployed Railway environment."""

from __future__ import annotations

import argparse
import io
import json
import os
import secrets
import sys
import urllib.error
import urllib.request
import zipfile


def request(
    method: str,
    url: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes]:
    prepared = urllib.request.Request(
        url,
        data=body,
        headers=headers or {},
        method=method,
    )
    try:
        with urllib.request.urlopen(prepared, timeout=120) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def json_request(
    method: str,
    url: str,
    payload: dict | None = None,
    token: str | None = None,
) -> tuple[int, dict]:
    headers = {"Accept": "application/json"}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    status, response_body = request(
        method,
        url,
        body=body,
        headers=headers,
    )
    return status, json.loads(response_body or b"{}")


def build_docx() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""",
        )
        archive.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""",
        )
        archive.writestr(
            "word/document.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>Smoke Test Candidate Python FastAPI SQL Docker</w:t></w:r></w:p></w:body>
</w:document>""",
        )
    return output.getvalue()


def multipart_docx(document: bytes) -> tuple[bytes, str]:
    boundary = f"railway-smoke-{secrets.token_hex(12)}"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="smoke-test.docx"\r\n'
        "Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n\r\n"
    ).encode("utf-8") + document + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, boundary


def expect(label: str, actual: int, expected: int) -> None:
    if actual != expected:
        raise RuntimeError(f"{label}: expected HTTP {expected}, received {actual}")
    print(f"PASS: {label} (HTTP {actual})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--confirm-target",
        action="store_true",
        help="Confirm that creating a temporary test user and history record is permitted.",
    )
    arguments = parser.parse_args()
    if not arguments.confirm_target:
        parser.error("--confirm-target is required; the script never runs implicitly")

    frontend_url = os.environ.get("FRONTEND_URL", "").rstrip("/")
    backend_url = os.environ.get("BACKEND_URL", "").rstrip("/")
    if not frontend_url.startswith("https://") or not backend_url.startswith("https://"):
        parser.error("FRONTEND_URL and BACKEND_URL must be explicit HTTPS URLs")

    suffix = secrets.token_hex(8)
    email = f"railway-smoke-{suffix}@example.invalid"
    password = f"Smoke-{secrets.token_urlsafe(24)}"

    expect("frontend loads", request("GET", frontend_url)[0], 200)
    expect("backend readiness", request("GET", f"{backend_url}/health")[0], 200)

    status, _ = json_request(
        "POST",
        f"{backend_url}/api/auth/register",
        {"name": "Railway Smoke Test", "email": email, "password": password},
    )
    expect("registration", status, 201)

    status, login = json_request(
        "POST",
        f"{backend_url}/api/auth/login",
        {"email": email, "password": password},
    )
    expect("login", status, 200)
    token = login.get("access_token")
    if not token:
        raise RuntimeError("login response did not contain an access token")

    expect(
        "current user",
        json_request("GET", f"{backend_url}/api/auth/me", token=token)[0],
        200,
    )
    expect(
        "unauthenticated parse rejected",
        request("POST", f"{backend_url}/api/resume/parse")[0],
        401,
    )

    document_body, boundary = multipart_docx(build_docx())
    parse_status, parse_body = request(
        "POST",
        f"{backend_url}/api/resume/parse",
        body=document_body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    expect("resume parsing and history creation", parse_status, 200)
    history_id = json.loads(parse_body).get("history_id")
    if not isinstance(history_id, int):
        raise RuntimeError("parse response did not contain a numeric history_id")

    expect(
        "history retrieval",
        json_request("GET", f"{backend_url}/api/history", token=token)[0],
        200,
    )
    expect(
        "history detail",
        json_request("GET", f"{backend_url}/api/history/{history_id}", token=token)[0],
        200,
    )
    expect(
        "created history deletion",
        json_request("DELETE", f"{backend_url}/api/history/{history_id}", token=token)[0],
        200,
    )

    print("Smoke checks passed. The generated test user remains because account deletion is unavailable.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1) from None
