"""``groq.AsyncGroq`` client factory.

The Groq SDK is stateless per call; a fresh ``AsyncGroq`` is cheap to build and
thread-safe. A factory keeps the API key confined to this module and out of
call sites and logs (ARC-007).
"""

from __future__ import annotations

import logging

from groq import AsyncGroq

from app.core.config import settings
from app.core.error_handlers import ServiceUnavailableError

logger = logging.getLogger(__name__)


def get_groq_client() -> AsyncGroq:
    """Return an ``AsyncGroq`` client configured with ``settings.GROQ_API_KEY``.

    Raises:
        ServiceUnavailableError: If the Groq API key is not configured.
    """
    if settings.GROQ_API_KEY is None:
        raise ServiceUnavailableError(
            "Groq API key is not configured.",
            context={"component": "groq_client"},
        )
    return AsyncGroq(api_key=settings.GROQ_API_KEY.get_secret_value())