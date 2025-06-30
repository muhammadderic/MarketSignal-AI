"""Global exception handlers producing the contract-compliant error envelope."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import correlation_id_ctx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain exception hierarchy (services raise these; handlers map to statuses)
# ---------------------------------------------------------------------------
class AppError(Exception):
    """Base class for domain exceptions carrying an HTTP status and code."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.context = context or {}


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "BAD_REQUEST"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"


class ExternalServiceError(AppError):
    """Third-party service failure (RSS, Groq, publisher site)."""

    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "EXTERNAL_SERVICE_ERROR"


class ServiceUnavailableError(AppError):
    """Upstream dependency temporarily unavailable (e.g. Groq rate limit)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"


class RateLimitError(AppError):
    """Upstream rate limit exhausted (HTTP 429)."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "RATE_LIMITED"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _envelope(
    *,
    detail: str | list[Any],
    error_code: str | None,
    request: Request,
    extra_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context: dict[str, Any] = {
        "request_id": correlation_id_ctx.get(),
        "path": request.url.path,
        "method": request.method,
    }
    if extra_context:
        context.update(extra_context)
    return {
        "detail": detail,
        "error_code": error_code,
        "timestamp": _utc_now_iso(),
        "context": context,
    }


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle FastAPI/Starlette ``HTTPException`` (includes default 404)."""
    detail = exc.detail if isinstance(exc.detail, (str, list)) else str(exc.detail)
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        502: "EXTERNAL_SERVICE_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    body = _envelope(
        detail=detail,
        error_code=code_map.get(exc.status_code, "HTTP_ERROR"),
        request=request,
    )
    return JSONResponse(status_code=exc.status_code, content=body)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation failures (HTTP 422)."""
    body = _envelope(
        detail=exc.errors(),
        error_code="VALIDATION_ERROR",
        request=request,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=body
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle all domain ``AppError`` subclasses with the mapped status code."""
    if exc.status_code >= 500:
        logger.error(
            "Application error: %s (code=%s, path=%s)",
            exc.detail,
            exc.error_code,
            request.url.path,
        )
    else:
        logger.warning(
            "Client error: %s (code=%s, path=%s)",
            exc.detail,
            exc.error_code,
            request.url.path,
        )
    body = _envelope(
        detail=exc.detail,
        error_code=exc.error_code,
        request=request,
        extra_context=exc.context,
    )
    return JSONResponse(status_code=exc.status_code, content=body)


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all for unexpected exceptions; logs and returns a 500 envelope."""
    logger.exception(
        "Unhandled exception on %s %s", request.method, request.url.path
    )
    body = _envelope(
        detail="Internal server error.",
        error_code="INTERNAL_ERROR",
        request=request,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to ``app``."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)