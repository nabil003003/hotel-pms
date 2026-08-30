"""Tests d'intégration contre la stack réelle (profil `core`). Ignorés si le
service n'est pas joignable."""

import os
import uuid

import httpx
import pytest

BASE_URL = os.environ.get("FRONT_OFFICE_URL", "http://localhost:8008")


def _service_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/healthz", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _service_reachable(),
    reason="front-office-service not reachable — start `docker compose --profile core up`",
)


async def test_healthz_ok():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200


async def test_check_in_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(
            "/api/v1/folios/check-in",
            json={"establishment_id": str(uuid.uuid4()), "booking_id": str(uuid.uuid4())},
        )
    assert resp.status_code == 401


async def test_reopen_always_forbidden_even_with_no_auth_returns_401_not_403():
    # Sans token -> 401 (dependency get_current_user s'exécute avant le corps
    # de l'endpoint) ; le 403 inconditionnel n'est atteint qu'authentifié.
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(f"/api/v1/folios/{uuid.uuid4()}/reopen")
    assert resp.status_code == 401
