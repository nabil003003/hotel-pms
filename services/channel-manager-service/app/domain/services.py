from __future__ import annotations

import hashlib
import hmac
import uuid
from collections import defaultdict
from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.domain.exceptions import (
    ConnectionNotFoundError,
    InvalidWebhookSignatureError,
    OtaConflictError,
    OtaMappingNotFoundError,
)
from app.domain.models import ChannelConnection, SyncLog
from app.events.publisher import publish_channel_booking_received, publish_channel_sync_failed
from app.infrastructure.crypto import encrypt
from app.infrastructure.establishment_client import get_ota_mapping
from app.infrastructure.reservation_client import ReservationBookingError, create_booking_from_ota

settings = get_settings()

# source `bookings.source` (reservation-service) n'a pas de valeur pour
# 'direct_website' — traité comme trafic direct plutôt qu'OTA (spec ligne
# 841, enum bookings.source).
OTA_NAME_TO_BOOKING_SOURCE = {
    "booking_com": "ota_booking",
    "expedia": "ota_expedia",
    "airbnb": "ota_airbnb",
    "direct_website": "website",
}

# ------------------------------------------------------------- connections --


async def create_or_update_connection(
    db: AsyncSession, establishment_id: uuid.UUID, *, ota_name: str, is_active: bool,
    credentials: str | None, two_way_sync_enabled: bool,
) -> ChannelConnection:
    stmt = select(ChannelConnection).where(
        ChannelConnection.establishment_id == establishment_id, ChannelConnection.ota_name == ota_name
    )
    existing = (await db.scalars(stmt)).first()
    if existing is not None:
        existing.is_active = is_active
        existing.two_way_sync_enabled = two_way_sync_enabled
        if credentials is not None:
            existing.credentials_encrypted = encrypt(credentials)
        connection = existing
    else:
        connection = ChannelConnection(
            id=uuid.uuid4(), establishment_id=establishment_id, ota_name=ota_name, is_active=is_active,
            two_way_sync_enabled=two_way_sync_enabled,
            credentials_encrypted=encrypt(credentials) if credentials else None,
        )
        db.add(connection)

    await db.commit()
    await db.refresh(connection)
    return connection


async def list_connections(db: AsyncSession, establishment_id: uuid.UUID) -> list[ChannelConnection]:
    stmt = select(ChannelConnection).where(ChannelConnection.establishment_id == establishment_id)
    result = await db.scalars(stmt)
    return list(result.all())


async def get_connection(db: AsyncSession, connection_id: uuid.UUID) -> ChannelConnection:
    connection = await db.get(ChannelConnection, connection_id)
    if connection is None:
        raise ConnectionNotFoundError(str(connection_id))
    return connection


# ------------------------------------------------------------------ webhook -


def _verify_signature(raw_body: bytes, signature: str) -> bool:
    expected = hmac.new(settings.webhook_hmac_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _split_guest_name(guest_name: str) -> tuple[str, str]:
    parts = guest_name.strip().split(" ", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")


async def process_webhook(
    db: AsyncSession, establishment_id: uuid.UUID, ota_name: str, *,
    raw_body: bytes, signature: str, correlation_id: str, payload: dict,
) -> dict:
    """Workflow C (spec ligne 307-321). Sprint 3 (D6) : appelle
    reservation-service en synchrone (`POST /api/v1/bookings`) pour créer
    une vraie réservation, conformément au contrat d'origine
    (`200 {internal_booking_id, status}`)."""
    if not _verify_signature(raw_body, signature):
        raise InvalidWebhookSignatureError("Invalid X-OTA-Signature")

    ota_reference = payload["ota_reference"]

    conflict_stmt = select(SyncLog).where(
        SyncLog.establishment_id == establishment_id,
        SyncLog.ota_name == ota_name,
        SyncLog.payload["ota_reference"].astext == ota_reference,
        SyncLog.status == "ok",
    )
    if (await db.scalars(conflict_stmt)).first() is not None:
        raise OtaConflictError(f"ota_reference {ota_reference} already processed")

    mapping = await get_ota_mapping(
        str(establishment_id), ota_name=ota_name, ota_room_type_id=payload.get("room_type_id")
    )
    if mapping is None:
        await publish_channel_sync_failed(establishment_id, ota_name, "MAPPING_ERROR", correlation_id)
        raise OtaMappingNotFoundError(f"No ota_mapping for room_type_id={payload.get('room_type_id')!r}")

    first_name, last_name = _split_guest_name(payload["guest_name"])
    booking_payload = {
        "market_segment_category": "OTA",
        "room_category": mapping.get("internal_room_category") or mapping["ota_room_type_id"],
        "check_in_date": payload["check_in"],
        "check_out_date": payload["check_out"],
        # Ni `regime` ni `taxes_payment_mode` ne figurent dans le payload OTA
        # standardisé du spec (ligne 288-301) — valeurs par défaut documentées.
        "regime": "BB",
        "taxes_payment_mode": "on_site",
        "adults": payload.get("adults", 1),
        "children": payload.get("children", 0),
        "customer": {
            "first_name": first_name, "last_name": last_name,
            "email": payload.get("guest_email"), "phone": payload.get("guest_phone"),
        },
        "source": OTA_NAME_TO_BOOKING_SOURCE.get(ota_name, "website"),
        "ota_reference": ota_reference,
    }

    error_status_code = None
    try:
        booking = await create_booking_from_ota(str(establishment_id), booking_payload)
        log_status, error_message = "ok", None
    except ReservationBookingError as exc:
        log_status, error_message, error_status_code = "error", str(exc.detail), exc.status_code

    log = SyncLog(
        id=uuid.uuid4(), establishment_id=establishment_id, ota_name=ota_name, event_type="booking_webhook",
        status=log_status, correlation_id=correlation_id, payload=payload, error_message=error_message,
    )
    db.add(log)

    connection_stmt = select(ChannelConnection).where(
        ChannelConnection.establishment_id == establishment_id, ChannelConnection.ota_name == ota_name
    )
    connection = (await db.scalars(connection_stmt)).first()
    if connection is not None and log_status == "ok":
        connection.last_sync_at = log.created_at

    await db.commit()

    if log_status == "error":
        await publish_channel_sync_failed(establishment_id, ota_name, error_message, correlation_id)
        if error_status_code == 409:
            raise OtaConflictError(error_message)
        raise OtaMappingNotFoundError(error_message)

    await publish_channel_booking_received(
        establishment_id, ota_name, ota_reference, correlation_id,
        {"internal_room_category": mapping.get("internal_room_category"), "internal_booking_id": booking["id"]},
    )

    return {"internal_booking_id": booking["id"], "status": booking["status"]}


# --------------------------------------------------------------- inbound ---


async def handle_booking_event(db: AsyncSession, routing_key: str, payload: dict) -> None:
    """Consommateur `booking.#` (D6) : reservation-service n'existe pas
    encore, donc aucune vraie mise à jour d'inventaire OTA n'est possible.
    On journalise pour chaque connexion OTA active de l'établissement afin
    de prouver le câblage RabbitMQ bout en bout (queue → handler → DB) sans
    fabriquer un push OTA qui n'existe pas."""
    establishment_id_raw = payload.get("establishment_id")
    if establishment_id_raw is None:
        return
    establishment_id = uuid.UUID(establishment_id_raw)

    connections = await list_connections(db, establishment_id)
    for connection in connections:
        if not connection.is_active:
            continue
        db.add(
            SyncLog(
                id=uuid.uuid4(), establishment_id=establishment_id, ota_name=connection.ota_name,
                event_type="inventory_update_pending", status="buffered",
                correlation_id=payload.get("correlation_id"),
                payload={"routing_key": routing_key, **payload},
            )
        )
    await db.commit()


# ------------------------------------------------------------- performance -


async def get_performance(db: AsyncSession, establishment_id: uuid.UUID, period: str) -> dict:
    """`GET /api/v1/channel/performance` (spec ligne 709, lu par
    analytics-service) — agrège `sync_logs` par OTA/statut sur le mois
    `period` (YYYY-MM)."""
    year, month = (int(part) for part in period.split("-"))
    month_start = date_type(year, month, 1)
    month_end = date_type(year + 1, 1, 1) if month == 12 else date_type(year, month + 1, 1)

    stmt = select(SyncLog).where(
        SyncLog.establishment_id == establishment_id,
        SyncLog.created_at >= month_start,
        SyncLog.created_at < month_end,
    )
    rows = (await db.scalars(stmt)).all()

    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        counts[row.ota_name][row.status] += 1

    return {"period": period, "by_ota": {ota: dict(statuses) for ota, statuses in counts.items()}}
