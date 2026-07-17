import logging

from app.config import settings
from app.performance import measured_call


def test_performance_logging_is_disabled_by_default(caplog) -> None:
    assert measured_call("unit_test", lambda: 42) == 42
    assert "performance operation=" not in caplog.text


def test_performance_logging_contains_no_call_data(monkeypatch, caplog) -> None:
    monkeypatch.setattr(settings, "performance_logging_enabled", True)
    with caplog.at_level(logging.INFO, logger="app.performance"):
        measured_call("safe_stage", lambda private_value: len(private_value), "secret text")

    assert "operation=safe_stage" in caplog.text
    assert "duration_ms=" in caplog.text
    assert "secret text" not in caplog.text
