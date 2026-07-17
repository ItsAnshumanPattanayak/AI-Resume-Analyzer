import logging
import time
from typing import Any, Callable
from contextlib import contextmanager
from collections.abc import Iterator

from app.config import settings


logger = logging.getLogger("app.performance")


@contextmanager
def measure_operation(operation: str) -> Iterator[None]:
    """Log one low-overhead operation duration when explicitly enabled."""

    if not settings.performance_logging_enabled:
        yield
        return

    started = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "performance operation=%s duration_ms=%.2f",
            operation,
            elapsed_ms,
        )


def measured_call(
    operation: str,
    function: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    with measure_operation(operation):
        return function(*args, **kwargs)
