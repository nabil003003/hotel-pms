from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.domain.exceptions import InvalidTransitionError, ReasonRequiredError, RoomNotFoundError
from app.domain.models import ALLOWED_TRANSITIONS, Room, RoomIncident, RoomStatusHistory
from app.events.publisher import publish_incident_reported, publish_status_changed
from app.infrastructure import reservation_client
from app.infrastructure.keycloak import get_service_token
from app.infrastructure.redis_client import publish_ws_message

settings = get_settings()


async def list_rooms(
    db: AsyncSession,
    establishment_id: uuid.UUID,
    *,
    statut: str | None = None,
    floor: int | None = None,
    categorie: str | None = None,
) -> list[Room]:
    stmt = select(Room).where(Room.establishment_id == establishment_id, Room.is_active.is_(True))
    if statut is not None:
        stmt = stmt.where(Room.statut == statut)
    if floor is not None:
        stmt = stmt.where(Room.floor == floor)
    if categorie is not None:
        stmt = stmt.where(Room.categorie == categorie)
    stmt = stmt.order_by(Room.floor, Room.numero)
    result = await db.scalars(stmt)
    return list(result.all())


async def get_room(db: AsyncSession, room_id: uuid.UUID) -> Room:
    room = await db.get(Room, room_id)
    if room is None:
        raise RoomNotFoundError(str(room_id))
    return room


UNBLOCK_ROLES = {"gouvernante", "manager", "admin"}


def is_unblock_allowed(roles: list[str], is_super_admin: bool) -> bool:
    """femme_de_chambre peut faire passer une chambre par tous les statuts
    sauf débloquer une chambre Bloquée -> Propre (§3.3 : lecture seule
    ailleurs, et le déblocage est une décision de supervision)."""
    if is_super_admin:
        return True
    return bool(set(roles) & UNBLOCK_ROLES)


def validate_transition(old_status: str, new_status: str) -> None:
    """Logique pure (pas d'I/O) — extraite pour être testée unitairement sans
    DB/Redis/RabbitMQ (plan Sprint 1 §5 : machine à états housekeeping)."""
    allowed = ALLOWED_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        raise InvalidTransitionError(old_status, new_status, sorted(allowed))


async def change_room_status(
    db: AsyncSession,
    room_id: uuid.UUID,
    *,
    new_status: str,
    reason: str | None,
    changed_by: uuid.UUID,
) -> Room:
    room = await get_room(db, room_id)
    old_status = room.statut

    validate_transition(old_status, new_status)

    if new_status == "Bloquée" and not reason:
        raise ReasonRequiredError("motif obligatoire pour blocage")

    room.statut = new_status
    if new_status == "Bloquée":
        room.motif_blocage = reason
        room.blocked_reason = reason
        room.blocked_by = changed_by
        room.blocked_at = datetime.now(timezone.utc)
    else:
        room.motif_blocage = None
        room.blocked_reason = None
        room.blocked_by = None
        room.blocked_at = None

    history = RoomStatusHistory(
        room_id=room.id, old_status=old_status, new_status=new_status, changed_by=changed_by, reason=reason
    )
    db.add(history)
    await db.commit()
    await db.refresh(room)

    payload = {
        "room_id": str(room.id),
        "establishment_id": str(room.establishment_id),
        "old_status": old_status,
        "new_status": new_status,
        "changed_by": str(changed_by),
    }
    await publish_status_changed(payload)
    await publish_ws_message(str(room.establishment_id), {"type": "room.status_changed", **payload})

    return room


async def create_incident(
    db: AsyncSession,
    room_id: uuid.UUID,
    establishment_id: uuid.UUID,
    *,
    incident_type: str,
    description: str | None,
    photo_url: str | None,
    reported_by: uuid.UUID,
) -> RoomIncident:
    room = await get_room(db, room_id)  # 404 si absent

    incident = RoomIncident(
        establishment_id=establishment_id,
        room_id=room_id,
        incident_type=incident_type,
        description=description,
        photo_url=photo_url,
        reported_by=reported_by,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)

    payload = {
        "room_id": str(room_id),
        "room_number": room.numero,
        "establishment_id": str(establishment_id),
        "incident_type": incident_type,
    }
    await publish_incident_reported(payload)
    await publish_ws_message(str(establishment_id), {"type": "room.incident_reported", **payload})

    return incident


async def list_incidents(db: AsyncSession, room_id: uuid.UUID) -> list[RoomIncident]:
    stmt = select(RoomIncident).where(RoomIncident.room_id == room_id).order_by(RoomIncident.reported_at.desc())
    result = await db.scalars(stmt)
    return list(result.all())


async def list_status_history(db: AsyncSession, room_id: uuid.UUID) -> list[RoomStatusHistory]:
    stmt = (
        select(RoomStatusHistory)
        .where(RoomStatusHistory.room_id == room_id)
        .order_by(RoomStatusHistory.changed_at.desc())
    )
    result = await db.scalars(stmt)
    return list(result.all())


# --------------------------------------------------------------------------
# Synchronisation avec establishment-service (décision D1)
# --------------------------------------------------------------------------


async def upsert_room_from_payload(db: AsyncSession, establishment_id: uuid.UUID, room_payload: dict) -> None:
    room_id = uuid.UUID(room_payload["id"])
    room = await db.get(Room, room_id)
    if room is None:
        room = Room(
            id=room_id,
            establishment_id=establishment_id,
            numero=room_payload["numero"],
            categorie=room_payload["categorie"],
            floor=room_payload["floor"],
            statut="Propre",
            is_active=room_payload.get("is_active", True),
        )
        db.add(room)
    else:
        room.numero = room_payload["numero"]
        room.categorie = room_payload["categorie"]
        room.floor = room_payload["floor"]
        room.is_active = room_payload.get("is_active", room.is_active)

    await db.commit()


async def handle_establishment_event(db: AsyncSession, routing_key: str, payload: dict) -> None:
    establishment_id = uuid.UUID(payload["establishment_id"])

    if routing_key == "establishment.created":
        return  # rien à faire : aucune chambre encore associée

    if routing_key == "establishment.rooms_imported":
        for room_payload in payload["rooms"]:
            await upsert_room_from_payload(db, establishment_id, room_payload)
        return

    if routing_key == "establishment.room_updated":
        await upsert_room_from_payload(db, establishment_id, payload["room"])
        return


# --------------------------------------------------------------------------
# Bascule fin de journée — consumer `audit.closed` (D12, Sprint 5)
# --------------------------------------------------------------------------

SYSTEM_ACTOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


async def apply_end_of_day_turnover(db: AsyncSession, establishment_id: uuid.UUID) -> int:
    """Spec ligne 645 : "housekeeping-service marque automatiquement toutes
    les chambres Occupée de la nuit J en Sale". `Room.statut` n'a pas de
    valeur "Occupée" (D12 — c'est reservation-service qui sait quelles
    chambres ont un séjour en cours, via `status_checked_in`), donc
    l'occupation est résolue par un appel REST plutôt qu'une lecture locale.
    Bascule forcée : contourne `validate_transition`/`ALLOWED_TRANSITIONS`
    délibérément (aucune de ces transitions n'autorise l'entrée dans "Sale"
    depuis Propre/Contrôlée — c'est un reset système, pas une action
    ménage). Les chambres déjà `Sale` ou `Bloquée` sont laissées inchangées."""
    room_ids = await reservation_client.get_checked_in_room_ids(str(establishment_id))
    turned = 0
    for room_id_str in room_ids:
        room = await db.get(Room, uuid.UUID(room_id_str))
        if room is None or room.statut in ("Sale", "Bloquée"):
            continue
        old_status = room.statut
        room.statut = "Sale"
        db.add(RoomStatusHistory(
            room_id=room.id, old_status=old_status, new_status="Sale", changed_by=SYSTEM_ACTOR_ID,
            reason="Night audit — bascule fin de journée automatique",
        ))
        await db.commit()
        await db.refresh(room)

        payload = {
            "room_id": str(room.id), "establishment_id": str(room.establishment_id),
            "old_status": old_status, "new_status": "Sale", "changed_by": str(SYSTEM_ACTOR_ID),
        }
        await publish_status_changed(payload)
        await publish_ws_message(str(room.establishment_id), {"type": "room.status_changed", **payload})
        turned += 1
    return turned


async def resync_from_establishment(db: AsyncSession, establishment_id: uuid.UUID) -> int:
    """Filet de sécurité REST (D1) — appelé si un événement RabbitMQ a pu être
    manqué. Récupère l'état complet des chambres depuis establishment-service."""
    token = await get_service_token()
    url = f"{settings.establishment_service_url}/api/v1/establishments/{establishment_id}/rooms"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
        rooms = resp.json()

    for room_payload in rooms:
        await upsert_room_from_payload(db, establishment_id, room_payload)

    return len(rooms)
