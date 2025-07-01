"""Baseline smoke test verifying the FastAPI app boots and health responds.

Assumes ``/api/v1/health`` is registered per ARCHITECTURE_SETUP.md §5 (AS-004).
"""

from __future__ import annotations

from httpx import AsyncClient


async def test_health_endpoint_returns_200(async_client: AsyncClient) -> None:
    """The health endpoint should return 200 OK with a JSON body."""
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)