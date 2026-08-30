"""Tests d'intégration contre la stack réelle (profil `core`). Ignorés si le
service n'est pas joignable."""

import os

import httpx
import pytest

BASE_URL = os.environ.get("PRICING_URL", "http://localhost:8004")


def _service_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/healthz", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _service_reachable(),
    reason="pricing-service not reachable — start `docker compose --profile core up`",
)


async def test_healthz_ok():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200


async def test_create_season_requires_auth():
    import uuid

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(
            f"/api/v1/pricing/{uuid.uuid4()}/seasons",
            json={"label": "Haute saison", "date_debut": "2026-06-01", "date_fin": "2026-09-01"},
        )
    assert resp.status_code == 401


async def test_rates_calculate_requires_auth():
    import uuid

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get(
            "/api/v1/rates/calculate",
            params={
                "establishment_id": str(uuid.uuid4()),
                "room_category": "Chambre Standard",
                "regime": "BB",
                "date_from": "2026-08-01",
                "date_to": "2026-08-03",
            },
        )
    assert resp.status_code == 401
