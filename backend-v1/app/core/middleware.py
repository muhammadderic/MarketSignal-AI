"""HTTP middleware for request correlation.

``RequestCorrelationMiddleware`` ensures every request carries an
``X-Request-ID`` — reusing an inbound value if present, generating a UUID4
otherwise — binds it to :data:`app.core.logging.correlation_id_ctx` for the
lifetime of the request, and echoes it back on the response.

This satisfies AC-005's correlation-ID requirement without altering response
bodies; error handlers read the same context var to embed ``request_id`` in
their ``context`` payloads.
"""

from __future__ import annotations

import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import correlation_id_ctx

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Bind / propagate an ``X-Request-ID`` for every inbound request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        token = correlation_id_ctx.set(request_id)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        finally:
            correlation_id_ctx.reset(token)

        response.headers[REQUEST_ID_HEADER] = request_id
        return response