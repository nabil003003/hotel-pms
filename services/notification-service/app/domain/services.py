from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import NotificationNotFoundError
from app.domain.models import Notification
from app.infrastructure.delivery import deliver


async def create_notification(
    db: AsyncSession, *, establishment_id: uuid.UUID, event_type: str, channel: str, recipient_role: str,
    subject: str, body: str, related_entity_id: uuid.UUID | None = None, payload: dict | None = None,
) -> Notification:
    """Point d'entrée unique (D11) — utilisé aussi bien par les handlers
    d'événements que par `POST /api/v1/notifications/send` (appels directs
    de night-audit-service)."""
    notification = Notification(
        id=uuid.uuid4(), establishment_id=establishment_id, event_type=event_type, channel=channel,
        recipient_role=recipient_role, subject=subject, body=body, related_entity_id=related_entity_id,
        payload=payload or {}, status="pending",
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    delivered = await deliver(channel=channel, recipient_role=recipient_role, subject=subject, body=body)
    notification.status = "sent" if delivered else "failed"
    if delivered:
        notification.sent_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notification)
    return notification


async def get_notification(db: AsyncSession, notification_id: uuid.UUID) -> Notification:
    notification = await db.get(Notification, notification_id)
    if notification is None:
        raise NotificationNotFoundError(str(notification_id))
    return notification


async def list_notifications(
    db: AsyncSession, establishment_id: uuid.UUID, *, event_type: str | None = None,
) -> list[Notification]:
    stmt = select(Notification).where(Notification.establishment_id == establishment_id)
    if event_type is not None:
        stmt = stmt.where(Notification.event_type == event_type)
    stmt = stmt.order_by(Notification.created_at.desc())
    result = await db.scalars(stmt)
    return list(result.all())


async def list_my_notifications(
    db: AsyncSession, establishment_id: uuid.UUID, *, recipient_roles: list[str], unread_only: bool = False,
) -> list[Notification]:
    """Scopé aux rôles de l'appelant (bannière de notifications du topbar) —
    contrairement à `list_notifications`, qui liste tout l'établissement pour
    la page Notifications (vue d'ensemble admin/manager)."""
    stmt = select(Notification).where(
        Notification.establishment_id == establishment_id, Notification.recipient_role.in_(recipient_roles)
    )
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    stmt = stmt.order_by(Notification.created_at.desc()).limit(50)
    result = await db.scalars(stmt)
    return list(result.all())


async def mark_notification_read(db: AsyncSession, notification_id: uuid.UUID) -> Notification:
    notification = await get_notification(db, notification_id)
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(notification)
    return notification


# ------------------------------------------------------------ event handlers


async def handle_booking_created(db: AsyncSession, payload: dict) -> None:
    """Spec ligne 320 : alerte réceptionniste à la réception d'une nouvelle
    réservation (chemin OTA notamment)."""
    guest = payload.get("customer_name") or f"réservation {payload['booking_id']}"
    await create_notification(
        db, establishment_id=uuid.UUID(payload["establishment_id"]), event_type="booking.created",
        channel="push", recipient_role="receptionniste", subject="Nouvelle réservation",
        body=f"Nouvelle réservation pour {guest} (segment {payload.get('segment')}).",
        related_entity_id=uuid.UUID(payload["booking_id"]),
    )


async def handle_booking_checked_in(db: AsyncSession, payload: dict) -> None:
    guest = payload.get("guest_name") or f"réservation {payload['booking_id']}"
    room = payload.get("room_number") or f"chambre {payload.get('room_id')}"
    await create_notification(
        db, establishment_id=uuid.UUID(payload["establishment_id"]), event_type="booking.checked_in",
        channel="push", recipient_role="receptionniste", subject="Check-in effectué",
        body=f"Check-in effectué pour {guest}, chambre {room}.",
        related_entity_id=uuid.UUID(payload["booking_id"]),
    )


async def handle_booking_checked_out(db: AsyncSession, payload: dict) -> None:
    """Spec ligne 523 : email de remerciement au client — pas un rôle
    interne, `recipient_role="client"` documente l'intention sans prétendre
    résoudre une vraie adresse (D11)."""
    guest = payload.get("guest_name")
    greeting = f"Merci pour votre séjour, {guest} !" if guest else "Merci pour votre séjour !"
    await create_notification(
        db, establishment_id=uuid.UUID(payload["establishment_id"]), event_type="booking.checked_out",
        channel="email", recipient_role="client", subject="Merci de votre séjour",
        body=greeting,
        related_entity_id=uuid.UUID(payload["booking_id"]),
    )


async def handle_booking_cancelled(db: AsyncSession, payload: dict) -> None:
    """Spec ligne 369 : "alerte si solde négatif" — condition non vérifiable
    ici (folio pas dans ce payload) ; simplification documentée (D11) :
    notifie systématiquement le manager, pas seulement en cas de solde
    négative."""
    guest = payload.get("customer_name") or f"réservation {payload['booking_id']}"
    await create_notification(
        db, establishment_id=uuid.UUID(payload["establishment_id"]), event_type="booking.cancelled",
        channel="push", recipient_role="manager", subject="Réservation annulée",
        body=f"Réservation de {guest} annulée ({payload.get('reason', 'raison non précisée')}).",
        related_entity_id=uuid.UUID(payload["booking_id"]),
    )


async def handle_room_incident_reported(db: AsyncSession, payload: dict) -> None:
    """Spec ligne 546 : notification push à la gouvernante."""
    room = payload.get("room_number") or f"#{payload['room_id']}"
    await create_notification(
        db, establishment_id=uuid.UUID(payload["establishment_id"]), event_type="room.incident_reported",
        channel="push", recipient_role="gouvernante", subject="Incident chambre signalé",
        body=f"Chambre {room} : incident {payload.get('incident_type')}.",
        related_entity_id=uuid.UUID(payload["room_id"]),
    )


async def handle_channel_sync_failed(db: AsyncSession, payload: dict) -> None:
    await create_notification(
        db, establishment_id=uuid.UUID(payload["establishment_id"]), event_type="channel.sync_failed",
        channel="email", recipient_role="admin", subject=f"Échec de synchronisation {payload.get('ota_name')}",
        body=f"Synchronisation {payload.get('ota_name')} en échec : {payload.get('error')}.",
    )
