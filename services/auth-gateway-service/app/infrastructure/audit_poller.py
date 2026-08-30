"""Poll Keycloak's Admin Events API and mirror LOGIN/LOGIN_ERROR events into
`auth_audit_log` (biom.txt deliverable) — Keycloak owns the real WebAuthn
credentials/sign-counters, this is purely a read-side audit trail.

No Keycloak Event Listener SPI (would need a Java provider + custom image)
and no dateFrom filtering (Keycloak's events query is day-granularity, too
coarse for a 15s poll) — instead we pull the latest N events every tick and
upsert on a synthesized dedup key, since the Admin REST API doesn't expose a
stable event id.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.keycloak import keycloak_admin
from app.domain.models import AuthAuditLog

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 15


def _dedup_key(event: dict[str, Any]) -> str:
    raw = "|".join(
        str(event.get(field, ""))
        for field in ("time", "type", "userId", "sessionId", "ipAddress")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def _poll_once() -> None:
    events = await keycloak_admin.list_events()
    if not events:
        return

    async with AsyncSessionLocal() as session:
        for event in events:
            user_id = event.get("userId")
            details = event.get("details") or {}
            stmt = (
                pg_insert(AuthAuditLog)
                .values(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(user_id) if user_id else None,
                    # Keycloak n'expose pas d'email sur l'event lui-même —
                    # "username" dans details est la meilleure approximation
                    # disponible (les comptes de ce realm sont provisionnés
                    # avec username == email, voir provision_user).
                    email=details.get("username"),
                    event_type=event.get("type", "UNKNOWN"),
                    error=event.get("error"),
                    ip_address=event.get("ipAddress"),
                    session_id=event.get("sessionId"),
                    occurred_at=datetime.fromtimestamp(event["time"] / 1000, tz=timezone.utc),
                    keycloak_event_id=_dedup_key(event),
                )
                .on_conflict_do_nothing(index_elements=["keycloak_event_id"])
            )
            await session.execute(stmt)
        await session.commit()


async def run_audit_poller() -> None:
    while True:
        try:
            await _poll_once()
        except Exception:  # noqa: BLE001
            logger.exception("auth_audit_log poll failed, retrying next tick")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
