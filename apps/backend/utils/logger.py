"""Structured logging configuration."""

import json
import logging
from datetime import datetime, timezone

from config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Get configured logger instance."""
    logger = logging.getLogger(name)

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = JSONFormatter()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger
