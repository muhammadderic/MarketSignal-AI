"""Structured logging configuration with secret redaction and correlation IDs.

Provides:
    * :data:`correlation_id_ctx` — a :class:`~contextvars.ContextVar` holding the
      active request correlation ID, bound by ``RequestCorrelationMiddleware``.
    * :class:`RedactingFilter` — a logging filter that masks credential-like keys
      in structured log fields before formatting.
    * :class:`JSONFormatter` — stdlib-compatible JSON log formatter.
    * :class:`DevelopmentFormatter` — ANSI-colored key/value formatter for local
      development.
    * :func:`setup_logging` — idempotent root-logger configuration entry point.
"""

from __future__ import annotations

import re
import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings



_SECRET_PATTERN = re.compile(
    r"(?i)\b(groq_api_key|authorization|cookie|api_key|secret|password|token)"
    r"(\s*[=:]\s*)([^\s,;]+)"
)

def _sanitize_exception_text(value: str) -> str:
    return _SECRET_PATTERN.sub(r"\1\2[REDACTED]", value)

# ----------------------------
#    Correlation ID context   
# ----------------------------
correlation_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)

# ---------------
   # Redaction   
# ---------------
REDACTED_VALUE = "[REDACTED]"
REDACTED_KEYS: frozenset[str] = frozenset(
    {
        "groq_api_key",
        "authorization",
        "cookie",
        "api_key",
        "secret",
        "password",
        "token",
    }
)

# Attributes set by ``logging.LogRecord`` itself. Everything else found on a
# record is treated as caller-supplied structured context.
_STANDARD_RECORD_ATTRS: frozenset[str] = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
        "message",
        "asctime",
    }
)


def _is_redacted_key(key: str) -> bool:
    """Return ``True`` when ``key`` (case-insensitive) is a sensitive field name."""
    return key.lower() in REDACTED_KEYS


def _redact(value: Any) -> Any:
    """Recursively replace values under sensitive keys with ``[REDACTED]``.

    Dict keys and nested structures are preserved. Lists are traversed in order.
    Scalars are returned unchanged.
    """
    if isinstance(value, dict):
        return {
            k: REDACTED_VALUE if _is_redacted_key(str(k)) else _redact(v)
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return type(value)(_redact(item) for item in value)
    return value


class RedactingFilter(logging.Filter):
    """Sanitize structured log fields before formatting.

    Applies to:
        * ``record.args`` when it is a dict (``logger.info("x", {"authorization": ...})``).
        * Any non-standard attribute on the record (i.e. ``extra={...}`` payloads),
          including a ``context`` dict.
        * ``record.msg`` when it is a dict (rare, but defensive).
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003 - stdlib API
        if isinstance(record.args, dict):
            record.args = _redact(record.args)

        if isinstance(record.msg, dict):
            record.msg = _redact(record.msg)

        for key, val in list(record.__dict__.items()):
            if key in _STANDARD_RECORD_ATTRS or key in {"args", "msg"}:
                continue
            if _is_redacted_key(key):
                record.__dict__[key] = REDACTED_VALUE
            else:
                record.__dict__[key] = _redact(val)

        # Ensure ``context`` is always a dict so JSON output is stable.
        if not isinstance(getattr(record, "context", None), dict):
            record.context = {}

        return True


# ----------------
#    Formatters   
# ----------------
def _utc_iso_from_epoch(created: float) -> str:
    """Convert a ``LogRecord.created`` epoch value to ISO 8601 UTC."""
    return datetime.fromtimestamp(created, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object.

    Output schema::

        {
          "timestamp": "<ISO-8601 UTC>",
          "level": "<LEVELNAME>",
          "logger": "<record.name>",
          "message": "<formatted message>",
          "correlation_id": "<uuid or null>",
          "context": { ... },
          "exception": "<traceback string, optional>"
        }
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": _utc_iso_from_epoch(record.created),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "context": getattr(record, "context", {}) or {},
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)

    def _format_exception_safely(
        self, record: logging.LogRecord
    ) -> str:
        exception_text = self.formatException(record.exc_info)
        return _sanitize_exception_text(exception_text)


class DevelopmentFormatter(logging.Formatter):
    """Human-friendly, ANSI-colored formatter for local development."""

    _LEVEL_COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }
    _RESET = "\033[0m"
    _DIM = "\033[2m"

    def format(self, record: logging.LogRecord) -> str:
        color = self._LEVEL_COLORS.get(record.levelname, "")
        cid = correlation_id_ctx.get() or "-"
        ts = _utc_iso_from_epoch(record.created)
        context = getattr(record, "context", {}) or {}
        ctx_suffix = f" {self._DIM}ctx={json.dumps(context, default=str)}{self._RESET}" if context else ""

        line = (
            f"{self._DIM}{ts}{self._RESET} "
            f"{color}{record.levelname:<8}{self._RESET} "
            f"{self._DIM}[{cid}]{self._RESET} "
            f"{record.name}: {record.getMessage()}{ctx_suffix}"
        )
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


# --------------
#   Bootstrap   
# --------------
_CONFIGURED_FLAG = "_marketsignal_logging_configured"


def _resolve_environment(override: str | None) -> str:
    env = (override or settings.ENVIRONMENT or "development").strip().lower()
    return "production" if env == "production" else "development"


def setup_logging(environment: str | None = None) -> None:
    """Configure the root logger once (idempotent).

    Args:
        environment: Optional override of ``settings.ENVIRONMENT``. When omitted,
            ``settings.ENVIRONMENT`` decides between JSON (``production``) and
            colorized (everything else) output.
    """
    root = logging.getLogger()
    if getattr(root, _CONFIGURED_FLAG, False):
        return

    env = _resolve_environment(environment)
    level_name = (settings.LOG_LEVEL or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.addFilter(RedactingFilter())
    handler.setFormatter(
        JSONFormatter() if env == "production" else DevelopmentFormatter()
    )

    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Application loggers inherit from root; silence noisy third-party loggers
    # unless explicitly raised by the caller.
    for noisy in ("uvicorn.error",):
        logging.getLogger(noisy).setLevel(level)

    setattr(root, _CONFIGURED_FLAG, True)