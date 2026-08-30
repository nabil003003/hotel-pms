"""Tests d'intégration contre la stack réelle (profil `core`). Ignorés si le
service n'est pas joignable."""

import os

import httpx
import pytest

BASE_URL = os.environ.get("HOUSEKEEPING_URL", "http://localhost:8003")


def _service_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/healthz", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _service_reachable(), reason="housekeeping-service not reachable — start `docker compose --profile core up`"
)


async def test_healthz_ok():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200


async def test_rooms_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get(
            "/api/v1/rooms", params={"establishment_id": "22222222-2222-2222-2222-222222222222"}
        )
    assert resp.status_code == 401
