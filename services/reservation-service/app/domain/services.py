from __future__ import annotations

import asyncio
import uuid
from datetime import date as date_type
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.domain.exceptions import (
    BookingNotFoundError,
    BusinessDateLockedError,
    CustomerNotFoundError,
    ElevationInvalidError,
    InvalidSegmentError,
    InvalidStatusTransitionError,
    MarketSegmentNotFoundError,
    NoRoomAvailableError,
    RoomConflictError,
    RoomShiftLockedError,
    RoomUnavailableError,
    UpsellRequiresValidationError,
)
from app.domain.models import AuditLog, Booking, BookingStatusHistory, BusinessDateLock, Customer, MarketSegment
from app.events.publisher import publish_booking_cancelled, publish_booking_created, publish_booking_room_changed
from app.infrastructure import establishment_client, pricing_client
from app.infrastructure import redis_client as locks
from app.infrastructure.auth_client import ElevationConsumptionError, consume_elevation

settings = get_settings()

# Acteur des transitions automatiques (job d'expiration d'option) — pas un
# vrai utilisateur, juste un marqueur reconnaissable dans booking_status_history.
SYSTEM_ACTOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

# status_no_show n'a aucun déclencheur décrit dans le spec (gap confirmé,
# voir D7) : transition manuelle uniquement, pas de job automatique inventé.
ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "status_option": {"status_confirmed", "status_voucher", "status_cancelled", "status_no_show"},
    "status_voucher": {"status_confirmed", "status_checked_in", "status_cancelled", "status_no_show"},
    "status_confirmed": {"status_voucher", "status_checked_in", "status_cancelled", "status_no_show"},
    "status_checked_in": {"status_checked_out"},
    "status_checked_out": set(),
    "status_no_show": set(),
    "status_cancelled": set(),
}


def _nights_between(check_in: date_type, check_out: date_type) -> list[date_type]:
    nights = []
    night = check_in
    while night < check_out:
        nights.append(night)
        night += timedelta(days=1)
    return nights


async def assert_business_date_not_locked(db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type) -> None:
    """D12 — même pattern que front-office-service (Sprint 4, D9) : le
    verrou n'est posé que par `handle_audit_closed` (consumer `audit.closed`
    publié par night-audit-service, Sprint 5)."""
    lock = await db.get(BusinessDateLock, (establishment_id, business_date))
    if lock is not None and lock.is_locked:
        raise BusinessDateLockedError(f"Business date {business_date} is locked for establishment {establishment_id}")


async def handle_audit_closed(db: AsyncSession, payload: dict) -> None:
    establishment_id = uuid.UUID(payload["establishment_id"])
    business_date = date_type.fromisoformat(payload["business_date"])
    lock = await db.get(BusinessDateLock, (establishment_id, business_date))
    if lock is None:
        db.add(BusinessDateLock(
            establishment_id=establishment_id, business_date=business_date, is_locked=True,
            locked_at=datetime.now(timezone.utc),
        ))
    else:
        lock.is_locked = True
        lock.locked_at = datetime.now(timezone.utc)
    await db.commit()


def _booking_to_dict(booking: Booking) -> dict:
    return {
        "id": str(booking.id),
        "establishment_id": str(booking.establishment_id),
        "customer_id": str(booking.customer_id),
        "room_id": str(booking.room_id),
        "market_segment_id": str(booking.market_segment_id),
        "status": booking.status,
        "check_in_date": booking.check_in_date.isoformat(),
        "check_out_date": booking.check_out_date.isoformat(),
        "regime": booking.regime,
        "partner_id": str(booking.partner_id) if booking.partner_id else None,
        "total_amount": float(booking.total_amount) if booking.total_amount is not None else None,
        "source": booking.source,
        "ota_reference": booking.ota_reference,
    }


# ---------------------------------------------------------- market segments -


async def create_market_segment(db: AsyncSession, establishment_id: uuid.UUID, **fields) -> MarketSegment:
    segment = MarketSegment(id=uuid.uuid4(), establishment_id=establishment_id, **fields)
    db.add(segment)
    await db.commit()
    await db.refresh(segment)
    return segment


async def get_market_segment(db: AsyncSession, segment_id: uuid.UUID) -> MarketSegment:
    segment = await db.get(MarketSegment, segment_id)
    if segment is None:
        raise MarketSegmentNotFoundError(str(segment_id))
    return segment


async def list_market_segments(db: AsyncSession, establishment_id: uuid.UUID) -> list[MarketSegment]:
    stmt = select(MarketSegment).where(
        MarketSegment.establishment_id == establishment_id, MarketSegment.is_active.is_(True)
    )
    result = await db.scalars(stmt)
    return list(result.all())


async def find_market_segment_by_category(
    db: AsyncSession, establishment_id: uuid.UUID, category: str
) -> MarketSegment:
    """Chemin OTA (D6) : channel-manager-service ne connaît que la
    catégorie (`OTA`), pas l'id exact d'un segment — résout le premier
    segment actif de cette catégorie plutôt que d'exiger que l'appelant le
    connaisse à l'avance."""
    stmt = select(MarketSegment).where(
        MarketSegment.establishment_id == establishment_id, MarketSegment.category == category,
        MarketSegment.is_active.is_(True),
    )
    segment = (await db.scalars(stmt)).first()
    if segment is None:
        raise MarketSegmentNotFoundError(f"No active {category!r} market segment for establishment {establishment_id}")
    return segment


async def update_market_segment(db: AsyncSession, segment_id: uuid.UUID, **fields) -> MarketSegment:
    segment = await get_market_segment(db, segment_id)
    for key, value in fields.items():
        if value is not None:
            setattr(segment, key, value)
    await db.commit()
    await db.refresh(segment)
    return segment


# ----------------------------------------------------------------- customers -


async def create_customer(db: AsyncSession, establishment_id: uuid.UUID, **fields) -> Customer:
    customer = Customer(id=uuid.uuid4(), establishment_id=establishment_id, **fields)
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


async def get_customer(db: AsyncSession, customer_id: uuid.UUID) -> Customer:
    customer = await db.get(Customer, customer_id)
    if customer is None:
        raise CustomerNotFoundError(str(customer_id))
    return customer


async def list_customers(db: AsyncSession, establishment_id: uuid.UUID, *, search: str | None = None) -> list[Customer]:
    stmt = select(Customer).where(
        Customer.establishment_id == establishment_id, Customer.anonymized_at.is_(None)
    )
    if search:
        tsvector = func.to_tsvector(
            "french", func.concat_ws(" ", Customer.first_name, Customer.last_name, func.coalesce(Customer.email, ""))
        )
        stmt = stmt.where(tsvector.op("@@")(func.plainto_tsquery("french", search)))
    result = await db.scalars(stmt.limit(50))
    return list(result.all())


async def update_customer(db: AsyncSession, customer_id: uuid.UUID, **fields) -> Customer:
    customer = await get_customer(db, customer_id)
    for key, value in fields.items():
        if value is not None:
            setattr(customer, key, value)
    await db.commit()
    await db.refresh(customer)
    return customer


async def find_or_create_customer(
    db: AsyncSession, establishment_id: uuid.UUID, *, first_name: str, last_name: str,
    email: str | None = None, phone: str | None = None,
) -> Customer:
    """Workflow C (spec ligne 314) : auto-création côté reservation-service
    quand l'OTA envoie un client inconnu. Recherche par email uniquement
    (seul identifiant fiable dans un payload OTA)."""
    if email:
        stmt = select(Customer).where(
            Customer.establishment_id == establishment_id, Customer.email == email, Customer.anonymized_at.is_(None)
        )
        existing = (await db.scalars(stmt)).first()
        if existing is not None:
            return existing
    return await create_customer(
        db, establishment_id, first_name=first_name, last_name=last_name, email=email, phone=phone
    )


# -------------------------------------------------------------- availability -


async def check_availability(
    db: AsyncSession, establishment_id: uuid.UUID, room_id: uuid.UUID, check_in_date: date_type,
    check_out_date: date_type, *, exclude_booking_id: uuid.UUID | None = None,
) -> uuid.UUID | None:
    """Prédicat de chevauchement standard — le spec ne donne aucune requête
    explicite pour ça (seulement le verrou Redis), donc c'est la logique de
    référence à tester unitairement. `status_checked_out` est exclu comme les
    statuts terminaux annulés : un séjour déjà terminé ne bloque plus la
    chambre pour les mêmes dates (sinon une chambre devient invendable à vie
    sur une plage de dates dès qu'un premier séjour s'y termine — bug réel
    trouvé Sprint 7 en rejouant le scénario E2E receptionniste)."""
    stmt = select(Booking.id).where(
        Booking.establishment_id == establishment_id,
        Booking.room_id == room_id,
        Booking.deleted_at.is_(None),
        Booking.status.notin_(["status_cancelled", "status_no_show", "status_checked_out"]),
        Booking.check_in_date < check_out_date,
        Booking.check_out_date > check_in_date,
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(Booking.id != exclude_booking_id)
    return (await db.scalars(stmt)).first()


# ------------------------------------------------------------------ bookings -


async def get_booking(db: AsyncSession, booking_id: uuid.UUID) -> Booking:
    booking = await db.get(Booking, booking_id)
    if booking is None or booking.deleted_at is not None:
        raise BookingNotFoundError(str(booking_id))
    return booking


async def list_bookings(
    db: AsyncSession, establishment_id: uuid.UUID, *, from_date: date_type | None = None,
    to_date: date_type | None = None, check_in_date: date_type | None = None,
    check_out_date: date_type | None = None, status: str | None = None,
) -> list[Booking]:
    stmt = select(Booking).where(Booking.establishment_id == establishment_id, Booking.deleted_at.is_(None))
    if from_date is not None:
        stmt = stmt.where(Booking.check_out_date > from_date)
    if to_date is not None:
        stmt = stmt.where(Booking.check_in_date < to_date)
    if check_in_date is not None:
        # Filtre exact (D12) — arrivées prévues J+1 (night-audit-service),
        # distinct du filtre de plage from_date/to_date ci-dessus.
        stmt = stmt.where(Booking.check_in_date == check_in_date)
    if check_out_date is not None:
        stmt = stmt.where(Booking.check_out_date == check_out_date)
    if status is not None:
        stmt = stmt.where(Booking.status == status)
    stmt = stmt.order_by(Booking.check_in_date)
    result = await db.scalars(stmt)
    return list(result.all())


async def create_booking(
    db: AsyncSession, establishment_id: uuid.UUID, *,
    market_segment_id: uuid.UUID | None, market_segment_category: str | None, room_category: str,
    room_id: uuid.UUID | None,
    check_in_date: date_type, check_out_date: date_type, regime: str, taxes_payment_mode: str,
    adults: int, children: int, notes: str | None,
    customer_id: uuid.UUID | None, customer: dict | None,
    partner_id: uuid.UUID | None, source: str, ota_reference: str | None, deposit_paid: bool,
    created_by: uuid.UUID,
) -> Booking:
    """Workflows A/B/C réunis (spec §4.1/4.2/4.3). `room_category` est
    toujours requis (nécessaire pour l'appel pricing-service, qui ne connaît
    que des catégories, jamais un `room_id`) ; `room_id` est optionnel — s'il
    est absent, une chambre libre de la catégorie est résolue automatiquement
    via establishment-service (chemin OTA, D6).

    Perf (Sprint 8, D15) : les deux appels HTTP sortants (establishment-service
    pour les chambres candidates, pricing-service pour le tarif) ne dépendent
    ni l'un de l'autre ni du reste du travail DB de cette fonction une fois
    `segment`/`requires_partner` connus — ils sont lancés en tâches de fond
    dès que possible et seulement `await`-és quand leur résultat devient
    nécessaire, au lieu d'être chaînés en série après la résolution complète
    de la chambre. `db` (AsyncSession) reste utilisé uniquement de façon
    séquentielle dans la coroutine principale : SQLAlchemy AsyncSession n'est
    pas sûr pour des awaits concurrents sur la même session."""
    room_candidates_task = (
        asyncio.create_task(establishment_client.get_rooms_by_category(str(establishment_id), room_category))
        if room_id is None else None
    )
    rate_task: asyncio.Task | None = None

    def _cancel_pending_tasks() -> None:
        for task in (room_candidates_task, rate_task):
            if task is not None and not task.done():
                task.cancel()

    try:
        await assert_business_date_not_locked(db, establishment_id, check_in_date)

        if market_segment_id is not None:
            segment = await get_market_segment(db, market_segment_id)
            if segment.establishment_id != establishment_id:
                raise InvalidSegmentError(f"Segment {market_segment_id} does not belong to establishment {establishment_id}")
        else:
            segment = await find_market_segment_by_category(db, establishment_id, market_segment_category)

        requires_partner = segment.category == "PARTENAIRES" or source == "b2b_agency"
        if requires_partner and partner_id is None:
            raise InvalidSegmentError("partner_id is required for a PARTENAIRES/b2b_agency booking")

        rate_task = asyncio.create_task(
            pricing_client.calculate_partner_rate(
                str(establishment_id), partner_id=str(partner_id), room_category=room_category, on_date=check_in_date
            )
            if requires_partner else
            pricing_client.calculate_public_rate(
                str(establishment_id), room_category=room_category, regime=regime,
                date_from=check_in_date, date_to=check_out_date,
            )
        )

        if customer_id is not None:
            cust = await get_customer(db, customer_id)
            if cust.establishment_id != establishment_id:
                raise CustomerNotFoundError(str(customer_id))
        elif customer is not None:
            cust = await find_or_create_customer(db, establishment_id, **customer)
        else:
            raise CustomerNotFoundError("customer_id or customer is required")

        if room_id is not None:
            target_room_id = room_id
        else:
            candidates = await room_candidates_task
            target_room_id = None
            for candidate in candidates:
                conflict = await check_availability(
                    db, establishment_id, uuid.UUID(candidate["id"]), check_in_date, check_out_date
                )
                if conflict is None:
                    target_room_id = uuid.UUID(candidate["id"])
                    break
            if target_room_id is None:
                raise NoRoomAvailableError(f"No available room in category {room_category!r} for the requested dates")
    except BaseException:
        _cancel_pending_tasks()
        raise

    nights = _nights_between(check_in_date, check_out_date)
    lock_keys = [locks.booking_lock_key(establishment_id, target_room_id, night) for night in nights]
    acquired = await locks.acquire_locks(lock_keys)
    if not acquired:
        _cancel_pending_tasks()
        raise RoomUnavailableError("Room is being booked concurrently by another request")

    try:
        conflict = await check_availability(db, establishment_id, target_room_id, check_in_date, check_out_date)
        if conflict is not None:
            _cancel_pending_tasks()
            raise RoomUnavailableError(f"Room {target_room_id} is unavailable for the requested dates")

        rate = await rate_task
        if requires_partner:
            # `tarif_negocie` est un prix par nuit (même sémantique que
            # rate_grid.prix_ttc) — contrairement à calculate_public_rate qui
            # renvoie déjà un total sommé sur le séjour.
            total_amount = float(rate["tarif_negocie"]) * len(nights) if rate else None
        else:
            total_amount = rate["total_ttc"] if rate else None

        if source.startswith("ota_"):
            status, option_expiry = "status_confirmed", None
        elif requires_partner:
            status, option_expiry = "status_voucher", None
        elif deposit_paid:
            status, option_expiry = "status_confirmed", None
        else:
            status = "status_option"
            option_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.option_expiry_hours)

        booking = Booking(
            id=uuid.uuid4(), establishment_id=establishment_id, customer_id=cust.id, room_id=target_room_id,
            market_segment_id=segment.id, status=status, option_expiry_date=option_expiry,
            check_in_date=check_in_date, check_out_date=check_out_date, regime=regime, partner_id=partner_id,
            taxes_payment_mode=taxes_payment_mode, total_amount=total_amount, adults=adults, children=children,
            notes=notes, source=source, ota_reference=ota_reference, created_by=created_by,
        )
        db.add(booking)
        db.add(
            BookingStatusHistory(
                id=uuid.uuid4(), booking_id=booking.id, old_status=None, new_status=status,
                changed_by=created_by, reason="Booking created",
            )
        )
        db.add(
            AuditLog(
                id=uuid.uuid4(), establishment_id=establishment_id, table_name="bookings", record_id=booking.id,
                action="INSERT", new_data=_booking_to_dict(booking), performed_by=created_by,
            )
        )
        await db.commit()
        await db.refresh(booking)
    finally:
        await locks.release_locks(lock_keys)

    # customer_name : uniquement pour un texte de notification lisible côté
    # notification-service — n'entre pas dans _booking_to_dict (utilisé aussi
    # pour l'audit log, dont le schéma ne doit pas changer pour ça).
    await publish_booking_created({**_booking_to_dict(booking), "customer_name": f"{cust.first_name} {cust.last_name}"})
    await locks.publish_ws_message(
        str(booking.establishment_id), {"type": "booking.created", "booking_id": str(booking.id)}
    )
    return booking


async def update_booking_status(
    db: AsyncSession, booking_id: uuid.UUID, new_status: str, *, changed_by: uuid.UUID,
    reason: str | None = None, correlation_id: uuid.UUID | None = None,
) -> Booking:
    booking = await get_booking(db, booking_id)
    old_status = booking.status
    if new_status not in ALLOWED_STATUS_TRANSITIONS.get(old_status, set()):
        raise InvalidStatusTransitionError(f"{old_status} -> {new_status} is not a legal transition")
    if new_status == "status_cancelled":
        # D12 : on ne peut pas annuler une réservation dont la date d'arrivée
        # est dans une journée déjà clôturée par night-audit-service.
        await assert_business_date_not_locked(db, booking.establishment_id, booking.check_in_date)

    booking.status = new_status
    if new_status != "status_option":
        booking.option_expiry_date = None

    db.add(
        BookingStatusHistory(
            id=uuid.uuid4(), booking_id=booking.id, old_status=old_status, new_status=new_status,
            changed_by=changed_by, reason=reason, correlation_id=correlation_id,
        )
    )
    db.add(
        AuditLog(
            id=uuid.uuid4(), establishment_id=booking.establishment_id, table_name="bookings",
            record_id=booking.id, action="UPDATE", old_data={"status": old_status},
            new_data={"status": new_status}, performed_by=changed_by,
        )
    )
    await db.commit()
    await db.refresh(booking)

    if new_status == "status_cancelled":
        cust = await get_customer(db, booking.customer_id)
        await publish_booking_cancelled(
            {**_booking_to_dict(booking), "customer_name": f"{cust.first_name} {cust.last_name}"}, reason
        )
        await locks.publish_ws_message(
            str(booking.establishment_id), {"type": "booking.cancelled", "booking_id": str(booking.id)}
        )
    return booking


async def expire_stale_options(db: AsyncSession) -> int:
    """Boucle asyncio en tâche de fond (main.py lifespan) — pas de Celery
    réel introduit pour ça (non-goal Sprint 3), même pattern que les
    consumers RabbitMQ existants."""
    now = datetime.now(timezone.utc)
    stmt = select(Booking.id).where(
        Booking.status == "status_option", Booking.option_expiry_date < now, Booking.deleted_at.is_(None)
    )
    ids = list((await db.scalars(stmt)).all())
    expired = 0
    for booking_id in ids:
        try:
            await update_booking_status(
                db, booking_id, "status_cancelled", changed_by=SYSTEM_ACTOR_ID, reason="Option expired"
            )
            expired += 1
        except InvalidStatusTransitionError:
            continue
    return expired


async def shift_room(
    db: AsyncSession, booking_id: uuid.UUID, *, new_room_id: uuid.UUID, new_room_category: str | None,
    new_check_in_date: date_type | None, new_check_out_date: date_type | None, same_category: bool,
    keep_current_rate: bool, force: bool, reason: str | None, elevation_token: str | None, actor: uuid.UUID,
) -> dict:
    """Workflow F (spec §4.6). D8 : `same_category` est fourni par
    l'appelant (le frontend connaît déjà les catégories via
    establishment-service pour rendre la grille planning) plutôt que
    résolu ici via un nouvel appel REST."""
    booking = await get_booking(db, booking_id)
    check_in = new_check_in_date or booking.check_in_date
    check_out = new_check_out_date or booking.check_out_date

    elevation_consumed = False

    async def _consume_elevation_or_raise() -> None:
        nonlocal elevation_consumed
        if elevation_consumed:
            return
        if not elevation_token:
            raise UpsellRequiresValidationError("This room shift requires manager elevation")
        try:
            await consume_elevation(elevation_token)
        except ElevationConsumptionError as exc:
            raise ElevationInvalidError(str(exc)) from exc
        elevation_consumed = True

    if not same_category:
        await _consume_elevation_or_raise()

    conflict = await check_availability(
        db, booking.establishment_id, new_room_id, check_in, check_out, exclude_booking_id=booking.id
    )
    if conflict is not None:
        if not force:
            raise RoomConflictError("Target room is occupied for the requested dates", conflicting_booking_id=conflict)
        # force est réservé aux managers — élévation requise même si la
        # catégorie n'a pas changé (D8).
        await _consume_elevation_or_raise()

    nights = _nights_between(check_in, check_out)
    lock_keys = [locks.room_shift_lock_key(booking.establishment_id, new_room_id, night) for night in nights]
    acquired = await locks.acquire_locks(lock_keys)
    if not acquired:
        raise RoomShiftLockedError("Room shift already in progress for this room/date range")

    try:
        old_room_id = booking.room_id
        old_amount = float(booking.total_amount) if booking.total_amount is not None else 0.0
        new_amount = booking.total_amount

        if not same_category and not keep_current_rate and new_room_category:
            rate = await pricing_client.calculate_public_rate(
                str(booking.establishment_id), room_category=new_room_category, regime=booking.regime,
                date_from=check_in, date_to=check_out,
            )
            if rate:
                new_amount = rate["total_ttc"]

        booking.room_id = new_room_id
        booking.check_in_date = check_in
        booking.check_out_date = check_out
        booking.total_amount = new_amount

        db.add(
            AuditLog(
                id=uuid.uuid4(), establishment_id=booking.establishment_id, table_name="bookings",
                record_id=booking.id, action="UPDATE",
                old_data={"room_id": str(old_room_id), "total_amount": old_amount},
                new_data={"room_id": str(new_room_id), "total_amount": float(new_amount) if new_amount is not None else None},
                performed_by=actor,
            )
        )
        await db.commit()
        await db.refresh(booking)
    finally:
        await locks.release_locks(lock_keys)

    delta = (float(new_amount) if new_amount is not None else 0.0) - old_amount
    await publish_booking_room_changed(_booking_to_dict(booking), old_room_id, new_room_id)
    await locks.publish_ws_message(
        str(booking.establishment_id),
        {
            "type": "booking.room_changed",
            "booking_id": str(booking.id),
            "old_room_id": str(old_room_id),
            "new_room_id": str(new_room_id),
        },
    )
    return {
        "booking_id": booking.id, "old_room_id": old_room_id, "new_room_id": new_room_id,
        "new_amount": booking.total_amount, "delta": round(delta, 2),
    }
