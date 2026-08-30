"""Tests d'intégration contre la stack réelle (profil `core` du docker-compose
racine). Ignorés automatiquement si le service n'est pas joignable — pour ne
pas casser un `pytest` lancé hors conteneur/CI sans la stack démarrée."""

import os

import httpx
import pytest

BASE_URL = os.environ.get("AUTH_GATEWAY_URL", "http://localhost:8001")


def _service_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/healthz", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _service_reachable(), reason="auth-gateway-service not reachable — start `docker compose --profile core up`"
)


async def test_healthz_ok():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_me_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_elevate_consume_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post("/api/v1/auth/elevate/consume", json={"token": "bogus"})
    assert resp.status_code == 401


async def test_audit_log_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get(
            "/api/v1/auth/establishments/22222222-2222-2222-2222-222222222222/audit-log"
        )
    assert resp.status_code == 401
