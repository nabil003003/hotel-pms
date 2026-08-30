"""Tests d'intégration contre la stack réelle (profil `core`). Ignorés si le
service n'est pas joignable."""

import os

import httpx
import pytest

BASE_URL = os.environ.get("ESTABLISHMENT_URL", "http://localhost:8002")


def _service_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/healthz", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _service_reachable(),
    reason="establishment-service not reachable — start `docker compose --profile core up`",
)


async def test_healthz_ok():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200


async def test_create_establishment_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post("/api/v1/establishments", json={"name": "Riad Test", "total_rooms": 5})
    assert resp.status_code == 401


async def test_ota_mappings_requires_auth():
    import uuid

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(
            f"/api/v1/establishments/{uuid.uuid4()}/ota-mappings",
            json={"ota_name": "booking_com", "ota_property_id": "123"},
        )
    assert resp.status_code == 401
