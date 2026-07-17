import threading
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request

from app.config import settings


@dataclass
class RateLimitEntry:
    window_started: float
    request_count: int


class InMemoryRateLimiter:
    """Thread-safe fixed-window limiter for one application process."""

    def __init__(self) -> None:
        self._entries: dict[str, RateLimitEntry] = {}
        self._lock = threading.Lock()

    def check(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
        now: float | None = None,
    ) -> int | None:
        current_time = time.monotonic() if now is None else now

        with self._lock:
            entry = self._entries.get(key)

            if (
                entry is None
                or current_time - entry.window_started
                >= window_seconds
            ):
                self._entries[key] = RateLimitEntry(
                    window_started=current_time,
                    request_count=1,
                )
                return None

            if entry.request_count >= limit:
                elapsed = current_time - entry.window_started
                return max(1, int(window_seconds - elapsed) + 1)

            entry.request_count += 1
            return None

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


rate_limiter = InMemoryRateLimiter()


def enforce_rate_limit(
    request: Request,
    *,
    category: str,
    limit: int,
) -> None:
    if not settings.rate_limit_enabled or settings.is_testing:
        return

    client_host = (
        request.client.host
        if request.client is not None
        else "unknown"
    )

    retry_after = rate_limiter.check(
        f"{category}:{client_host}",
        limit=limit,
        window_seconds=settings.rate_limit_window_seconds,
    )

    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
