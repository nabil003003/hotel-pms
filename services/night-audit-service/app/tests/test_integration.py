"""Tests d'intégration contre la stack réelle (profil `core`). Ignorés si le
service n'est pas joignable."""

import os
import uuid

import httpx
import pytest

BASE_URL = os.environ.get("NIGHT_AUDIT_URL", "http://localhost:8010")


def _service_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/healthz", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _service_reachable(),
    reason="night-audit-service not reachable — start `docker compose --profile core up`",
)


async def test_healthz_ok():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200


async def test_verify_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(
            "/api/v1/night-audit/verify",
            json={"establishment_id": str(uuid.uuid4()), "business_date": "2026-01-01"},
        )
    assert resp.status_code == 401


async def test_close_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(
            "/api/v1/night-audit/close",
            json={"establishment_id": str(uuid.uuid4()), "business_date": "2026-01-01"},
            headers={"X-Audit-Token": "not-a-real-token"},
        )
    assert resp.status_code == 401


async def test_business_date_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get(
            "/api/v1/night-audit/business-date", params={"establishment_id": str(uuid.uuid4())}
        )
    assert resp.status_code == 401
