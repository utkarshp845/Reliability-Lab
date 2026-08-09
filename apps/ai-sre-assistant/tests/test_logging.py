import json
import logging
from pathlib import Path

from fastapi.testclient import TestClient

from app.logging_config import logger
from app.main import app


client = TestClient(app)


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _records_by_event(handler: CaptureHandler) -> dict[str, logging.LogRecord]:
    return {record.event: record for record in handler.records if hasattr(record, "event")}


def test_json_formatter_emits_the_shared_service_shape():
    formatter = logger.handlers[0].formatter
    record = logging.LogRecord(
        name="ai-sre-assistant",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="analysis_completed",
        args=(),
        exc_info=None,
    )
    record.event = "analysis_completed"
    record.request_id = "req-1"

    payload = json.loads(formatter.format(record))

    assert payload["service"] == "ai-sre-assistant"
    assert payload["level"] == "INFO"
    assert payload["event"] == "analysis_completed"
    assert payload["request_id"] == "req-1"
    assert "timestamp" in payload


def test_request_id_header_is_returned_and_generated_when_missing():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_request_id_header_is_echoed_and_logged():
    handler = CaptureHandler()
    logger.addHandler(handler)

    try:
        response = client.get("/health", headers={"x-request-id": "sre-request-123"})
    finally:
        logger.removeHandler(handler)

    assert response.headers["x-request-id"] == "sre-request-123"

    records = _records_by_event(handler)
    assert records["request_completed"].request_id == "sre-request-123"
    assert records["request_completed"].status_code == 200


def test_analyze_logs_reports_correlated_request_ids_from_demo_service_evidence(tmp_path: Path, monkeypatch):
    log_file = tmp_path / "demo-service.log"
    log_file.write_text(
        '{"level":"ERROR","event":"simulated_error","message":"boom","endpoint":"/simulate/error","request_id":"demo-req-1"}\n'
        '{"level":"WARNING","event":"simulated_latency","message":"slow","endpoint":"/simulate/latency","duration_ms":1200,"request_id":"demo-req-2"}\n'
        '{"level":"INFO","event":"request_completed","message":"done","path":"/simulate/error","status_code":500,"request_id":"demo-req-1"}\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("DEMO_SERVICE_LOG_PATH", str(log_file))

    handler = CaptureHandler()
    logger.addHandler(handler)

    try:
        response = client.post(
            "/analyze/logs",
            json={"max_lines": 20, "use_llm": False},
            headers={"x-request-id": "sre-request-abc"},
        )
    finally:
        logger.removeHandler(handler)

    assert response.status_code == 200
    body = response.json()
    assert body["correlated_request_ids"] == ["demo-req-1", "demo-req-2"]
    assert body["rule_based_analysis"]["correlated_request_ids"] == ["demo-req-1", "demo-req-2"]
    assert any(item.get("request_id") in {"demo-req-1", "demo-req-2"} for item in body["rule_based_analysis"]["evidence"])

    records = _records_by_event(handler)
    completed = records["analysis_completed"]
    assert completed.correlated_request_ids == ["demo-req-1", "demo-req-2"]
    assert completed.request_id == "sre-request-abc"


def test_analyze_logs_reports_no_correlated_request_ids_when_evidence_has_none(tmp_path: Path, monkeypatch):
    log_file = tmp_path / "demo-service.log"
    log_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("DEMO_SERVICE_LOG_PATH", str(log_file))

    response = client.post("/analyze/logs", json={"max_lines": 20, "use_llm": False})

    assert response.status_code == 200
    assert response.json()["correlated_request_ids"] == []
