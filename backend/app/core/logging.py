"""Structured (JSON) logging configuration."""

from __future__ import annotations

import logging
import sys

try:  # python-json-logger >= 3.1 moved the formatter to .json
    from pythonjsonlogger.json import JsonFormatter
except ImportError:  # pragma: no cover - older releases
    from pythonjsonlogger.jsonlogger import JsonFormatter

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """Install a JSON formatter on the root logger (idempotent)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Align uvicorn's loggers with our JSON handler.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
