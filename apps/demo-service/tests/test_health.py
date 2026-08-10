import json
import logging

from fastapi.testclient import TestClient

from app.logging_config import logger
from app.main import app
from app.metrics import METRICS


client = TestClient(app)


class CaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def setup_function():
    METRICS.reset()


def test_health_endpoint_returns_healthy_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "demo-service"}


def test_metrics_endpoint_returns_prometheus_text():
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "demo_service_http_requests_total" in response.text
    assert "demo_service_http_request_duration_seconds_bucket" in response.text


def test_metrics_normalize_dynamic_order_paths():
    client.get("/api/orders/ord-1001")

    response = client.get("/metrics")

    assert 'path="/api/orders/{order_id}"' in response.text
    assert "ord-1001" not in response.text


def test_metrics_include_simulation_counters():
    client.get("/simulate/error?probability=1.0")
    client.get("/simulate/latency?min_ms=0&max_ms=1")
    client.get("/simulate/memory-pressure?size_mb=1")

    response = client.get("/metrics")

    assert 'demo_service_simulated_errors_total{endpoint="/simulate/error",error_type="checkout_dependency_timeout"} 1' in response.text
    assert 'demo_service_simulated_latency_events_total{endpoint="/simulate/latency"} 1' in response.text
    assert 'demo_service_memory_pressure_events_total{endpoint="/simulate/memory-pressure"} 1' in response.text
    assert 'status_code="500"' in response.text


def test_request_id_header_is_returned_and_used_in_route_logs():
    handler = CaptureHandler()
    logger.addHandler(handler)

    try:
        response = client.get("/simulate/error?probability=1.0", headers={"x-request-id": "demo-request-123"})
    finally:
        logger.removeHandler(handler)

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "demo-request-123"

    records_by_event = {record.event: record for record in handler.records if hasattr(record, "event")}
    assert records_by_event["simulated_error"].request_id == "demo-request-123"
    assert records_by_event["request_completed"].request_id == "demo-request-123"
    assert records_by_event["request_completed"].status_code == 500


def test_request_id_header_is_generated_when_missing():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_json_formatter_excludes_asyncio_task_name():
    # Python 3.12+ asyncio sets LogRecord.taskName on records logged from
    # inside a task (e.g. the request middleware). It is a stdlib internal
    # detail, not an application field, and must not leak into the log line.
    formatter = logger.handlers[0].formatter
    record = logging.LogRecord(
        name="demo-service",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    record.event = "request_completed"
    record.taskName = "Task-7"

    payload = json.loads(formatter.format(record))

    assert "taskName" not in payload
