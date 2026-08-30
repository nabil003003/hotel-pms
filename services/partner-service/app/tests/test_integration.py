"""Tests d'intégration contre la stack réelle (profil `core`). Ignorés si le
service n'est pas joignable."""

import os
import uuid

import httpx
import pytest

BASE_URL = os.environ.get("PARTNER_URL", "http://localhost:8005")


def _service_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/healthz", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _service_reachable(),
    reason="partner-service not reachable — start `docker compose --profile core up`",
)


async def test_healthz_ok():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200


async def test_create_partner_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(
            f"/api/v1/partners/{uuid.uuid4()}", json={"type": "AGENCE", "nom": "Agence Test"}
        )
    assert resp.status_code == 401


async def test_list_partners_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get(f"/api/v1/partners/{uuid.uuid4()}")
    assert resp.status_code == 401
