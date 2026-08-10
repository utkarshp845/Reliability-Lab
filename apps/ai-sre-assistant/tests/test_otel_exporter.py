import logging

import pytest

from app.logging_config import setup_logging
from app.otel_exporter import (
    OTLPHttpLogHandler,
    build_handler_from_env,
    build_otlp_payload,
    get_otlp_endpoint,
    get_otlp_timeout_seconds,
    record_to_otlp_log,
)


def _make_record(level: int = logging.INFO, **extra) -> logging.LogRecord:
    record = logging.LogRecord(
        name="ai-sre-assistant",
        level=level,
        pathname=__file__,
        lineno=1,
        msg="analysis_completed",
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_get_otlp_endpoint_is_disabled_when_unset(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)

    assert get_otlp_endpoint() is None


def test_get_otlp_endpoint_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318/")

    assert get_otlp_endpoint() == "http://otel-collector:4318"


def test_get_otlp_timeout_seconds_falls_back_on_bad_value(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TIMEOUT_SECONDS", "not-a-number")

    assert get_otlp_timeout_seconds() == pytest.approx(1.0)


def test_record_to_otlp_log_maps_severity_and_attributes():
    record = _make_record(
        level=logging.WARNING,
        event="analysis_completed",
        request_id="sre-req-1",
        logs_read=42,
        correlated_request_ids=["demo-req-1", "demo-req-2"],
    )

    otlp_record = record_to_otlp_log(record)

    assert otlp_record["severityText"] == "WARNING"
    assert otlp_record["severityNumber"] == 13
    attributes = {item["key"]: item["value"] for item in otlp_record["attributes"]}
    assert attributes["request_id"] == {"stringValue": "sre-req-1"}
    assert attributes["logs_read"] == {"intValue": "42"}
    # Non-primitive extras (lists, dicts) fall back to their string form,
    # same as JsonFormatter's `default=str` behavior for non-JSON-native types.
    assert attributes["correlated_request_ids"] == {"stringValue": "['demo-req-1', 'demo-req-2']"}


def test_record_to_otlp_log_excludes_asyncio_task_name():
    # Python 3.12+ asyncio sets LogRecord.taskName on records logged from
    # inside a task (e.g. the request middleware). It is a stdlib internal
    # detail, not an application field, and must not leak into evidence.
    record = _make_record(event="request_completed")
    record.taskName = "Task-7"

    otlp_record = record_to_otlp_log(record)

    keys = {item["key"] for item in otlp_record["attributes"]}
    assert "taskName" not in keys


def test_build_otlp_payload_shape_carries_service_name():
    record = _make_record(event="request_completed")

    payload = build_otlp_payload([record], service_name="ai-sre-assistant")

    resource_attrs = payload["resourceLogs"][0]["resource"]["attributes"]
    assert {"key": "service.name", "value": {"stringValue": "ai-sre-assistant"}} in resource_attrs
    assert payload["resourceLogs"][0]["scopeLogs"][0]["scope"]["name"] == "ai-sre-assistant"


def test_build_handler_from_env_returns_none_when_disabled(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)

    assert build_handler_from_env(service_name="ai-sre-assistant") is None


def test_build_handler_from_env_returns_handler_when_enabled(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")

    handler = build_handler_from_env(service_name="ai-sre-assistant")

    assert isinstance(handler, OTLPHttpLogHandler)
    assert handler.url == "http://otel-collector:4318/v1/logs"


def test_emit_posts_the_built_payload_to_the_logs_endpoint(monkeypatch):
    handler = OTLPHttpLogHandler(service_name="ai-sre-assistant", endpoint="http://otel-collector:4318")
    calls = []
    monkeypatch.setattr(
        "app.otel_exporter.httpx.post",
        lambda url, json, timeout: calls.append((url, json, timeout)),
    )

    handler.emit(_make_record(event="analysis_completed", request_id="sre-req-9"))

    assert len(calls) == 1
    url, payload, timeout = calls[0]
    assert url == "http://otel-collector:4318/v1/logs"
    assert timeout == handler.timeout
    assert payload["resourceLogs"][0]["resource"]["attributes"][0]["value"]["stringValue"] == "ai-sre-assistant"


def test_emit_swallows_export_failures_without_raising(monkeypatch):
    handler = OTLPHttpLogHandler(service_name="ai-sre-assistant", endpoint="http://otel-collector:4318", timeout=0.1)

    def _raise(*args, **kwargs):
        raise ConnectionError("collector unreachable")

    monkeypatch.setattr("app.otel_exporter.httpx.post", _raise)
    monkeypatch.setattr(handler, "handleError", lambda record: None)

    handler.emit(_make_record(event="analysis_completed"))


def test_setup_logging_skips_otlp_handler_by_default(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)

    logger = setup_logging()

    assert not any(isinstance(h, OTLPHttpLogHandler) for h in logger.handlers)


def test_setup_logging_attaches_otlp_handler_when_configured(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")

    try:
        logger = setup_logging()
        assert any(isinstance(h, OTLPHttpLogHandler) for h in logger.handlers)
    finally:
        # Restore the default (no-OTLP) logger so later tests in this
        # process aren't left pointed at a fake collector endpoint.
        monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
        setup_logging()
