"""Per-item fault isolation for external service calls (ARC-006).

Wraps async callables so that network and SDK failures are translated into
the project's existing domain exceptions rather than propagating raw third
party exceptions or aborting unrelated work. The wrapped callable's arguments
and return value are passed through unchanged.
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Awaitable, Callable, TypeVar

import groq
import httpx

from app.core.error_handlers import (
    ExternalServiceError,
    RateLimitError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _safe_url(exc: BaseException) -> str | None:
    """Extract a URL host from an httpx exception without leaking query strings."""
    request = getattr(exc, "request", None)
    if request is not None and request.url is not None:
        return request.url.host
    return None


def async_fault_handler(
    service_name: str,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator mapping external-service failures to domain exceptions.

    Mapping:
        * ``httpx.TimeoutException`` / ``httpx.NetworkError`` →
          ``ExternalServiceError`` (502).
        * ``httpx.HTTPStatusError`` with 429 → ``RateLimitError`` (429).
        * ``httpx.HTTPStatusError`` with 5xx → ``ServiceUnavailableError`` (503).
        * ``httpx.HTTPStatusError`` with other 4xx → ``ExternalServiceError`` (502).
        * ``groq.RateLimitError`` → ``RateLimitError`` (429).
        * ``groq.APIConnectionError`` / ``groq.APIStatusError`` →
          ``ServiceUnavailableError`` (503).

    Logged context deliberately excludes headers, settings, and raw exception
    messages that could contain credentials.
    """

    def decorator(
        func: Callable[..., Awaitable[T]],
    ) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except httpx.TimeoutException as exc:
                logger.warning(
                    "External call timed out",
                    extra={"context": {
                        "service": service_name,
                        "exception": type(exc).__name__,
                        "host": _safe_url(exc),
                    }},
                )
                raise ExternalServiceError(
                    f"{service_name} request timed out.",
                    context={"service": service_name,
                             "reason": type(exc).__name__},
                ) from exc
            except httpx.NetworkError as exc:
                logger.warning(
                    "External call network error",
                    extra={"context": {
                        "service": service_name,
                        "exception": type(exc).__name__,
                        "host": _safe_url(exc),
                    }},
                )
                raise ExternalServiceError(
                    f"{service_name} network error.",
                    context={"service": service_name,
                             "reason": type(exc).__name__},
                ) from exc
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                logger.warning(
                    "External call HTTP error",
                    extra={"context": {
                        "service": service_name,
                        "status_code": status,
                        "host": _safe_url(exc),
                    }},
                )
                if status == 429:
                    raise RateLimitError(
                        f"{service_name} rate limit exceeded.",
                        context={"service": service_name, "status_code": status},
                    ) from exc
                if status >= 500:
                    raise ServiceUnavailableError(
                        f"{service_name} is unavailable.",
                        context={"service": service_name, "status_code": status},
                    ) from exc
                raise ExternalServiceError(
                    f"{service_name} rejected the request.",
                    context={"service": service_name, "status_code": status},
                ) from exc
            except groq.RateLimitError as exc:
                logger.warning(
                    "Groq rate limit",
                    extra={"context": {"service": service_name,
                                       "exception": type(exc).__name__}},
                )
                raise RateLimitError(
                    f"{service_name} rate limit exceeded.",
                    context={"service": service_name},
                ) from exc
            except (groq.APIConnectionError, groq.APIStatusError) as exc:
                logger.warning(
                    "Groq API error",
                    extra={"context": {"service": service_name,
                                       "exception": type(exc).__name__}},
                )
                raise ServiceUnavailableError(
                    f"{service_name} is unavailable.",
                    context={"service": service_name,
                             "reason": type(exc).__name__},
                ) from exc

        return wrapper

    return decorator