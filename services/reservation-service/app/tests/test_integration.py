"""Tests d'intégration contre la stack réelle (profil `core`). Ignorés si le
service n'est pas joignable."""

import os
import uuid

import httpx
import pytest

BASE_URL = os.environ.get("RESERVATION_URL", "http://localhost:8007")


def _service_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/healthz", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _service_reachable(),
    reason="reservation-service not reachable — start `docker compose --profile core up`",
)


async def test_healthz_ok():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200


async def test_create_booking_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(
            "/api/v1/bookings",
            json={
                "establishment_id": str(uuid.uuid4()),
                "market_segment_id": str(uuid.uuid4()),
                "room_category": "Chambre Standard",
                "check_in_date": "2026-08-01",
                "check_out_date": "2026-08-03",
                "regime": "BB",
                "taxes_payment_mode": "on_site",
                "adults": 2,
                "customer": {"first_name": "Test", "last_name": "Guest"},
            },
        )
    assert resp.status_code == 401


async def test_check_availability_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(
            "/api/v1/bookings/check-availability",
            json={
                "establishment_id": str(uuid.uuid4()),
                "room_id": str(uuid.uuid4()),
                "check_in_date": "2026-08-01",
                "check_out_date": "2026-08-03",
            },
        )
    assert resp.status_code == 401
