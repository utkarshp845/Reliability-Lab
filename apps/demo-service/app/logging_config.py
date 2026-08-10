import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.otel_exporter import build_handler_from_env


SERVICE_NAME = "demo-service"
DEFAULT_LOG_PATH = "logs/demo-service.log"

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


def get_log_path() -> Path:
    return Path(os.getenv("DEMO_SERVICE_LOG_PATH", DEFAULT_LOG_PATH))


class JsonFormatter(logging.Formatter):
    """Format log records as compact JSON so machines and humans can inspect them."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_ATTRS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, separators=(",", ":"), default=str)


def setup_logging() -> logging.Logger:
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(SERVICE_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = JsonFormatter()

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)

    otlp_handler = build_handler_from_env(service_name=SERVICE_NAME)
    if otlp_handler is not None:
        logger.addHandler(otlp_handler)

    return logger


logger = setup_logging()

