"""Structured JSON logger factory for BookRover.

Produces CloudWatch-compatible JSON log output. Every log line is a single
JSON object, suitable for structured querying in CloudWatch Logs Insights.

Usage:
    from bookrover.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Sale created", extra={"sale_id": sale_id})

Security: never log PII — no phone numbers, no full names.
"""

import json
import logging
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects for CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a log record to JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON string with level, message, timestamp, and logger fields.
        """
        log_object: dict = {
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "logger": record.name,
        }
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_object)


def get_logger(name: str) -> logging.Logger:
    """Return a JSON-structured logger for the given module name.

    Idempotent — calling with the same name returns the same logger without
    adding duplicate handlers.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        Configured Logger instance with JSON output to stderr.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger
