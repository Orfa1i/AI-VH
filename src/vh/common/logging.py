"""
Structured JSON logging module for AI Virtual Hospital (AI-VH).
Outputs standard JSON log records with automatic run_id, step, and context propagation.
"""

import contextvars
import json
import logging
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Generator, Optional

_LOG_CONTEXT: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "vh_log_context", default={}
)


def get_log_context() -> Dict[str, Any]:
    """Retrieve current contextual logging metadata."""
    return _LOG_CONTEXT.get()


def set_log_context(run_id: Optional[str] = None, step: Optional[str] = None, **kwargs: Any) -> None:
    """Set global or thread-local logging context fields."""
    ctx = dict(_LOG_CONTEXT.get())
    if run_id is not None:
        ctx["run_id"] = run_id
    if step is not None:
        ctx["step"] = step
    ctx.update(kwargs)
    _LOG_CONTEXT.set(ctx)


def clear_log_context() -> None:
    """Reset contextual logging metadata to empty dictionary."""
    _LOG_CONTEXT.set({})


@contextmanager
def log_context(run_id: Optional[str] = None, step: Optional[str] = None, **kwargs: Any) -> Generator[None, None, None]:
    """Context manager to scope run_id, step, and custom fields to a block of execution."""
    prev_ctx = _LOG_CONTEXT.get()
    new_ctx = dict(prev_ctx)
    if run_id is not None:
        new_ctx["run_id"] = run_id
    if step is not None:
        new_ctx["step"] = step
    new_ctx.update(kwargs)
    token = _LOG_CONTEXT.set(new_ctx)
    try:
        yield
    finally:
        _LOG_CONTEXT.reset(token)


class JSONFormatter(logging.Formatter):
    """Formats log records into single-line JSON strings with structured telemetry fields."""

    def format(self, record: logging.LogRecord) -> str:
        ctx = get_log_context()
        timestamp = datetime.now(timezone.utc).isoformat()

        payload: Dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": ctx.get("run_id"),
            "step": ctx.get("step"),
            "file": record.filename,
            "line": record.lineno,
        }

        # Include custom extra kwargs if present on record
        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message"
        }
        for attr, value in record.__dict__.items():
            if attr not in standard_attrs and not attr.startswith("_"):
                payload[attr] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def setup_json_logging(level: str = "INFO") -> None:
    """Configure root logger with JSONFormatter stream handler."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing stream handlers to prevent duplicates
    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.StreamHandler):
            root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Obtain a named logger configured for AI-VH structured telemetry."""
    return logging.getLogger(name)
