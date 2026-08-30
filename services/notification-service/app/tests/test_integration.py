"""Tests d'intégration contre la stack réelle (profil `core`). Ignorés si le
service n'est pas joignable."""

import os
import uuid

import httpx
import pytest

BASE_URL = os.environ.get("NOTIFICATION_URL", "http://localhost:8011")


def _service_reachable() -> bool:
    try:
        httpx.get(f"{BASE_URL}/healthz", timeout=1.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _service_reachable(),
    reason="notification-service not reachable — start `docker compose --profile core up`",
)


async def test_healthz_ok():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200


async def test_list_notifications_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/api/v1/notifications", params={"establishment_id": str(uuid.uuid4())})
    assert resp.status_code == 401


async def test_send_requires_auth():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post(
            "/api/v1/notifications/send",
            json={
                "establishment_id": str(uuid.uuid4()),
                "event_type": "test.event",
                "channel": "email",
                "recipient_role": "admin",
                "subject": "test",
                "body": "test",
            },
        )
    assert resp.status_code == 401
