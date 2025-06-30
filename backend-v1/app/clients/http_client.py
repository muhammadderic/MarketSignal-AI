"""Singleton ``httpx.AsyncClient`` lifecycle and dependency provider.

The client is bound to the FastAPI application lifespan (``init_http_client``
on startup, ``close_http_client`` on shutdown) so all outbound HTTP reuses a
single pooled connection set. Blocking clients are forbidden (ARC-002).
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.core.error_handlers import ServiceUnavailableError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
DEFAULT_LIMITS = httpx.Limits(
    max_keepalive_connections=20, max_connections=100
)
DEFAULT_USER_AGENT = "MarketSignalAI/1.0 (+https://marketsignal.local)"

_http_client: Optional[httpx.AsyncClient] = None


async def init_http_client() -> None:
    """Create the shared ``httpx.AsyncClient``. Idempotent."""
    global _http_client
    if _http_client is not None:
        return
    _http_client = httpx.AsyncClient(
        timeout=DEFAULT_TIMEOUT,
        limits=DEFAULT_LIMITS,
        headers={"User-Agent": DEFAULT_USER_AGENT},
    )
    logger.info(
        "Shared httpx.AsyncClient initialized",
        extra={"context": {"connect_timeout": 10.0, "read_timeout": 30.0}},
    )


async def close_http_client() -> None:
    """Close and clear the shared ``httpx.AsyncClient``. Idempotent."""
    global _http_client
    if _http_client is None:
        return
    await _http_client.aclose()
    _http_client = None
    logger.info("Shared httpx.AsyncClient closed")


def get_http_client() -> httpx.AsyncClient:
    """FastAPI dependency returning the shared client.

    Raises:
        ServiceUnavailableError: If the client was not initialized (i.e. the
            dependency is requested outside the application lifespan).
    """
    if _http_client is None:
        raise ServiceUnavailableError(
            "HTTP client is not initialized.",
            context={"component": "http_client"},
        )
    return _http_client