from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import async_engine
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestCorrelationMiddleware
from app.clients.http_client import close_http_client, init_http_client

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage async engine resources across the application lifecycle."""
    await init_http_client()
    logger.info(
        "MarketSignal AI API starting", extra={"context": {"env": settings.ENVIRONMENT}}
    )
    try:
        yield
    finally:
        await async_engine.dispose()
        await close_http_client()
        logger.info("MarketSignal AI API shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# === MIDDLEWARES ===
# Middleware order note: Starlette applies middleware in reverse registration
# order, so the correlation middleware is registered *after* CORS to sit closer
# to the application (innermost). This ensures the X-Request-ID header is set on
# responses before CORS headers are appended, and that exception handlers (which
# read correlation_id_ctx) observe the populated value.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestCorrelationMiddleware)


# === GLOBAL ERROR HANDLER ===
register_exception_handlers(app)


# === ROUTES ===
app.include_router(api_router, prefix="/api/v1")