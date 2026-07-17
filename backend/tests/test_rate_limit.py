import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.config import settings
from app.rate_limit import InMemoryRateLimiter, enforce_rate_limit, rate_limiter


def build_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/auth/login",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )


def test_limiter_blocks_and_resets() -> None:
    limiter = InMemoryRateLimiter()

    assert limiter.check("client", limit=2, window_seconds=60, now=0) is None
    assert limiter.check("client", limit=2, window_seconds=60, now=1) is None
    assert limiter.check("client", limit=2, window_seconds=60, now=2) == 59
    assert limiter.check("client", limit=2, window_seconds=60, now=60) is None


def test_endpoint_limiter_returns_429(monkeypatch) -> None:
    request = build_request()
    monkeypatch.setattr(settings, "app_environment", "development")
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)
    rate_limiter.clear()

    enforce_rate_limit(request, category="test", limit=1)

    with pytest.raises(HTTPException) as error:
        enforce_rate_limit(request, category="test", limit=1)

    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"]


def test_endpoint_limiter_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_enabled", False)

    for _ in range(20):
        enforce_rate_limit(build_request(), category="disabled", limit=1)
