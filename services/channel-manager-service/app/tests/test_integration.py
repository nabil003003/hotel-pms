"""Tests d'intégration contre la stack réelle (profil `core`). Ignorés si le
service n'est pas joignable."""

import os
import uuid

import httpx
import pytest

BASE_URL = os.environ.get("CHANNEL_MANAGER_URL", "http://localhost:8006")


def _service_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/healthz", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _service_reachable(),
    reason="channel-manager-service not reachable — start `docker compose --profile core up`",
)


async def test_healthz_ok():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200


async def test_create_connection_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(
            f"/api/v1/channel/connections/{uuid.uuid4()}", json={"ota_name": "booking_com"}
        )
    assert resp.status_code == 401


async def test_webhook_rejects_bad_signature():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(
            "/api/v1/channel/webhook/booking_com",
            params={"establishment_id": str(uuid.uuid4())},
            headers={"X-OTA-Signature": "deadbeef"},
            json={
                "ota_reference": "TEST123",
                "property_id": "prop-1",
                "room_type_id": "std",
                "guest_name": "Test Guest",
                "check_in": "2026-08-01",
                "check_out": "2026-08-03",
                "total_amount": 1000,
                "status": "new",
            },
        )
    assert resp.status_code == 401
