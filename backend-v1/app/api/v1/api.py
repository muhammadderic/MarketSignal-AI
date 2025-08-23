"""Aggregate router for all ``/api/v1`` endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    archive,
    articles,
    health,
    ingestion,
    relevance,
    resolver,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ingestion.router)
api_router.include_router(archive.router)
api_router.include_router(articles.router)
api_router.include_router(relevance.router)
api_router.include_router(resolver.router)
