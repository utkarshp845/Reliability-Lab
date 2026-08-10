import logging
import os
from typing import Any

import httpx


DEFAULT_TIMEOUT_SECONDS = 1.0

# Kept in sync with logging_config._RESERVED_LOG_ATTRS by hand. Duplicated
# rather than imported so this module has no import-time dependency on
# logging_config (which itself builds a handler from this module at import
# time) - that would otherwise be a circular import.
_RESERVED_LOG_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}

# OpenTelemetry log severity numbers. See the OTel logs data model spec:
# TRACE=1-4, DEBUG=5-8, INFO=9-12, WARN=13-16, ERROR=17-20, FATAL=21-24.
_SEVERITY_NUMBERS = {
    logging.DEBUG: 5,
    logging.INFO: 9,
    logging.WARNING: 13,
    logging.ERROR: 17,
    logging.CRITICAL: 21,
}


def get_otlp_endpoint() -> str | None:
    """Read the optional collector endpoint, e.g. http://otel-collector:4318.

    Unset (the default) disables OTLP export entirely so the dependency-light
    quickstart never depends on a collector being present.
    """
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    return endpoint.rstrip("/") or None


def get_otlp_timeout_seconds() -> float:
    raw = os.getenv("OTEL_EXPORTER_OTLP_TIMEOUT_SECONDS", "")
    try:
        return float(raw) if raw else DEFAULT_TIMEOUT_SECONDS
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def _attribute_value(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int):
        return {"intValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    return {"stringValue": str(value)}


def record_to_otlp_log(record: logging.LogRecord) -> dict[str, Any]:
    """Convert one log record into an OTLP JSON logRecord.

    Reuses the same extra-field pickup JsonFormatter uses, so a collector
    receives exactly the fields the local JSON log line already carries.
    """
    attributes = [
        {"key": key, "value": _attribute_value(value)}
        for key, value in record.__dict__.items()
        if key not in _RESERVED_LOG_ATTRS and not key.startswith("_") and value is not None
    ]

    time_unix_nano = str(int(record.created * 1_000_000_000))

    return {
        "timeUnixNano": time_unix_nano,
        "observedTimeUnixNano": time_unix_nano,
        "severityNumber": _SEVERITY_NUMBERS.get(record.levelno, 9),
        "severityText": record.levelname,
        "body": {"stringValue": record.getMessage()},
        "attributes": attributes,
    }


def build_otlp_payload(records: list[logging.LogRecord], service_name: str) -> dict[str, Any]:
    return {
        "resourceLogs": [
            {
                "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": service_name}}]},
                "scopeLogs": [
                    {
                        "scope": {"name": service_name},
                        "logRecords": [record_to_otlp_log(record) for record in records],
                    }
                ],
            }
        ]
    }


class OTLPHttpLogHandler(logging.Handler):
    """Best-effort OTLP/HTTP JSON log exporter for an optional local collector.

    This sends one record per HTTP POST, synchronously, on whatever thread
    calls the logger. That is a deliberate simplification for a teaching lab:
    a production exporter batches records and ships them off the request path
    (the OTel SDK's BatchLogRecordProcessor does exactly that). Keep the
    timeout short and never let an export failure or a slow/unreachable
    collector raise out of application code.
    """

    def __init__(self, service_name: str, endpoint: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        super().__init__()
        self.service_name = service_name
        self.url = f"{endpoint}/v1/logs"
        self.timeout = timeout

    def emit(self, record: logging.LogRecord) -> None:
        try:
            payload = build_otlp_payload([record], service_name=self.service_name)
            httpx.post(self.url, json=payload, timeout=self.timeout)
        except Exception:  # noqa: BLE001 - a handler must never let export break logging.
            self.handleError(record)


def build_handler_from_env(service_name: str) -> OTLPHttpLogHandler | None:
    endpoint = get_otlp_endpoint()
    if not endpoint:
        return None
    return OTLPHttpLogHandler(service_name=service_name, endpoint=endpoint, timeout=get_otlp_timeout_seconds())
