"""Aggregate router for all ``/api/v1`` endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import health, ingestion

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ingestion.router)
