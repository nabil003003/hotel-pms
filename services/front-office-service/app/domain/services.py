from __future__ import annotations

import uuid
from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import (
    BusinessDateLockedError,
    CatalogItemNotFoundError,
    FolioNotBalancedError,
    FolioNotFoundError,
    FolioNotOpenError,
    InvalidBookingStateError,
    RoomNotReadyError,
)
from app.domain.models import BusinessDateLock, Folio, FolioCharge, Payment
from app.events.publisher import (
    publish_booking_checked_in,
    publish_booking_checked_out,
    publish_folio_charge_added,
    publish_payment_added,
)
from app.infrastructure import housekeeping_client, night_audit_client, pricing_client
from app.infrastructure.reservation_client import (
    ReservationClientError,
    get_booking,
    get_customer,
    update_booking_status,
)

# Table Workflow E (spec ligne 421-435) — taux TVA fixe par poste comptable.
# REM (remise) et TS/TPT (taxes fixes/pax) sont à 0% par définition du spec.
POSTE_TVA_RATES: dict[str, float] = {
    "HEB": 10, "PDJ": 10, "RES": 10, "DIN": 10,
    "BAR": 20, "SPA": 20, "ACT": 20, "HAM": 20, "TRF": 20, "EXC": 20,
    "TS": 0, "TPT": 0, "REM": 0,
}

ROOM_READY_STATUSES = {"Propre", "Contrôlée"}


def _amounts_from_ht(unit_price_ht: float, quantity: int, tva_rate: float) -> tuple[float, float, float]:
    montant_ht = round(float(unit_price_ht) * quantity, 2)
    tva_amount = round(montant_ht * float(tva_rate) / 100, 2)
    return montant_ht, tva_amount, round(montant_ht + tva_amount, 2)


def _amounts_from_ttc(montant_ttc: float, tva_rate: float) -> tuple[float, float, float]:
    montant_ht = round(float(montant_ttc) / (1 + float(tva_rate) / 100), 2)
    tva_amount = round(float(montant_ttc) - montant_ht, 2)
    return montant_ht, tva_amount, round(float(montant_ttc), 2)


# ---------------------------------------------------------------- folios ---


async def get_folio(db: AsyncSession, folio_id: uuid.UUID) -> Folio:
    folio = await db.get(Folio, folio_id)
    if folio is None:
        raise FolioNotFoundError(str(folio_id))
    return folio


async def list_folios_for_booking(db: AsyncSession, booking_id: uuid.UUID) -> list[Folio]:
    stmt = select(Folio).where(Folio.booking_id == booking_id)
    result = await db.scalars(stmt)
    return list(result.all())


async def assert_business_date_not_locked(
    db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type
) -> None:
    """D9 : ce verrou n'est posé que par `handle_audit_closed` (consumer
    `audit.closed`), donc toujours `is_locked=False` tant que
    night-audit-service (Sprint 5) n'existe pas — câblé pour de vrai, pas
    encore déclenchable en pratique avant ce sprint."""
    lock = await db.get(BusinessDateLock, (establishment_id, business_date))
    if lock is not None and lock.is_locked:
        raise BusinessDateLockedError(
            f"La date métier du {business_date.strftime('%d/%m/%Y')} est verrouillée (clôture déjà effectuée)."
        )


def _create_charge_row(
    db: AsyncSession, folio: Folio, *, poste_comptable: str, libelle: str, quantity: int, unit_price_ht: float,
    actor: uuid.UUID, business_date: date_type, source_service: str | None = None,
    catalog_item_id: uuid.UUID | None = None,
) -> FolioCharge:
    tva_rate = POSTE_TVA_RATES[poste_comptable]
    montant_ht, tva_amount, montant_ttc = _amounts_from_ht(unit_price_ht, quantity, tva_rate)
    charge = FolioCharge(
        id=uuid.uuid4(), folio_id=folio.id, poste_comptable=poste_comptable, libelle=libelle, quantity=quantity,
        unit_price_ht=unit_price_ht, montant_ht=montant_ht, tva_rate=tva_rate, tva_amount=tva_amount,
        montant_ttc=montant_ttc, source_service=source_service, catalog_item_id=catalog_item_id,
        created_by=actor, business_date=business_date,
    )
    db.add(charge)
    folio.total_charges = round(float(folio.total_charges) + montant_ttc, 2)
    folio.version += 1
    return charge


async def _auto_charge_stay(db: AsyncSession, folio: Folio, booking: dict, actor: uuid.UUID) -> list[FolioCharge]:
    """Charges automatiques posées à l'ouverture du Folio A : HEB (montant
    de la réservation, ligne unique — pas de ventilation nuit par nuit en
    Sprint 4) + TS/TPT (fixe par pax x nuits, lu depuis pricing-service).
    Retourne les lignes créées pour que l'appelant publie `folio.charge_added`
    une fois le commit fait (analytics-service en a besoin pour le CA)."""
    created: list[FolioCharge] = []

    if booking.get("total_amount") is not None:
        tva_rate = POSTE_TVA_RATES["HEB"]
        montant_ht, tva_amount, montant_ttc = _amounts_from_ttc(float(booking["total_amount"]), tva_rate)
        charge = FolioCharge(
            id=uuid.uuid4(), folio_id=folio.id, poste_comptable="HEB", libelle="Hébergement (séjour)", quantity=1,
            unit_price_ht=montant_ht, montant_ht=montant_ht, tva_rate=tva_rate, tva_amount=tva_amount,
            montant_ttc=montant_ttc, source_service="front-office-auto", created_by=actor,
            business_date=folio.business_date,
        )
        db.add(charge)
        folio.total_charges = round(float(folio.total_charges) + montant_ttc, 2)
        folio.version += 1
        created.append(charge)
    # sinon : pricing-service était indisponible à la création de la
    # réservation (D7) — pas de ligne HEB automatique, le réceptionniste
    # devra en ajouter une manuellement.

    check_in_date = date_type.fromisoformat(booking["check_in_date"])
    check_out_date = date_type.fromisoformat(booking["check_out_date"])
    nights = (check_out_date - check_in_date).days
    pax = int(booking["adults"]) + int(booking["children"])

    taxes = await pricing_client.get_ts_tpt_taxes(booking["establishment_id"])
    for tax in taxes:
        amount_per_pax = float(tax["taux_ou_montant"])
        created.append(
            _create_charge_row(
                db, folio, poste_comptable=tax["type"], libelle=f"{tax['type']} ({pax} pers. x {nights} nuits)",
                quantity=pax * nights, unit_price_ht=amount_per_pax, actor=actor, business_date=folio.business_date,
                source_service="front-office-auto",
            )
        )

    return created


async def check_in(db: AsyncSession, establishment_id: uuid.UUID, booking_id: uuid.UUID, *, actor: uuid.UUID) -> dict:
    """Workflow D (spec §4.4, lignes 353-397)."""
    try:
        booking = await get_booking(str(booking_id))
    except ReservationClientError as exc:
        raise InvalidBookingStateError(f"Could not read booking {booking_id}: {exc}") from exc

    if booking["establishment_id"] != str(establishment_id):
        raise InvalidBookingStateError(f"Booking {booking_id} does not belong to establishment {establishment_id}")
    if booking["status"] not in ("status_confirmed", "status_voucher"):
        raise InvalidBookingStateError(f"Booking status {booking['status']!r} does not allow check-in")

    room = await housekeeping_client.get_room(booking["room_id"])
    if room["statut"] not in ROOM_READY_STATUSES:
        raise RoomNotReadyError(f"Chambre non prête. Statut actuel: {room['statut']}")

    # Date métier réelle (night-audit), pas `date.today()` : une clôture
    # avance `business_date` au-delà du calendrier, et `date.today()`
    # désignerait alors une journée déjà verrouillée pour ce folio.
    today = await night_audit_client.get_business_date(str(establishment_id))
    await assert_business_date_not_locked(db, establishment_id, today)

    # Étape 2 (table saga, ligne 390) : créer Folio A (+B) — committé seul
    # d'abord ; compensation = soft-delete si l'étape 3 échoue.
    folio_a = Folio(
        id=uuid.uuid4(), establishment_id=establishment_id, booking_id=booking_id, type="A", status="open",
        business_date=today, created_by=actor, total_charges=0, total_payments=0, version=1,
    )
    db.add(folio_a)
    folios = [folio_a]

    partner_id = booking.get("partner_id")
    folio_b = None
    if partner_id:
        folio_b = Folio(
            id=uuid.uuid4(), establishment_id=establishment_id, booking_id=booking_id, type="B", status="open",
            third_party_ref=uuid.UUID(partner_id), business_date=today, created_by=actor,
            total_charges=0, total_payments=0, version=1,
        )
        db.add(folio_b)
        folios.append(folio_b)

    auto_charges = await _auto_charge_stay(db, folio_a, booking, actor)
    await db.commit()
    for folio in folios:
        await db.refresh(folio)

    # Étape 3 (table saga) : changer le statut réservation. Échec ->
    # compensation = fermeture des folios tout juste créés (pas de colonne
    # deleted_at sur folios dans le schéma transcrit — fermeture en tient lieu).
    try:
        await update_booking_status(str(booking_id), "status_checked_in")
    except ReservationClientError as exc:
        for folio in folios:
            folio.status = "closed"
            folio.closed_at = datetime.now(timezone.utc)
            folio.closed_by = actor
        await db.commit()
        raise InvalidBookingStateError(f"Failed to transition booking to checked_in, folios compensated: {exc}") from exc

    customer = await get_customer(str(establishment_id), booking["customer_id"])
    await publish_booking_checked_in(
        str(booking_id), booking["room_id"], [str(f.id) for f in folios], str(establishment_id), today.isoformat(),
        guest_name=f"{customer['first_name']} {customer['last_name']}", room_number=room["numero"],
    )
    for charge in auto_charges:
        await publish_folio_charge_added(
            str(charge.id), str(booking_id), float(charge.montant_ttc), charge.poste_comptable,
            str(establishment_id), today.isoformat(),
        )
    return {"booking_id": booking_id, "folio_ids": [f.id for f in folios]}


async def add_charge(
    db: AsyncSession, folio_id: uuid.UUID, *, poste_comptable: str, libelle: str, quantity: int,
    unit_price_ht: float | None, catalog_item_id: uuid.UUID | None, source_service: str | None, actor: uuid.UUID,
) -> FolioCharge:
    """Workflow E (spec §4.5, lignes 400-436)."""
    folio = await get_folio(db, folio_id)
    if folio.status != "open":
        raise FolioNotOpenError(f"Folio {folio_id} is not open")
    await assert_business_date_not_locked(db, folio.establishment_id, folio.business_date)

    if catalog_item_id is not None:
        item = await pricing_client.get_extras_catalog_item(str(folio.establishment_id), str(catalog_item_id))
        if item is None:
            raise CatalogItemNotFoundError(f"Catalog item {catalog_item_id} not found")
        unit_price_ht = float(item["prix_ht"])  # prix catalogue fait foi, pas celui du client ("vérifié contre catalogue")
    if unit_price_ht is None:
        raise CatalogItemNotFoundError("unit_price_ht or catalog_item_id is required")

    charge = _create_charge_row(
        db, folio, poste_comptable=poste_comptable, libelle=libelle, quantity=quantity, unit_price_ht=unit_price_ht,
        actor=actor, business_date=folio.business_date, source_service=source_service, catalog_item_id=catalog_item_id,
    )
    await db.commit()
    await db.refresh(folio)
    await db.refresh(charge)
    await publish_folio_charge_added(
        str(charge.id), str(folio.booking_id), float(charge.montant_ttc), charge.poste_comptable,
        str(folio.establishment_id), folio.business_date.isoformat(),
    )
    return charge


async def add_payment(
    db: AsyncSession, folio_id: uuid.UUID, *, mode: str, montant: float, reference: str | None, actor: uuid.UUID,
) -> Payment:
    folio = await get_folio(db, folio_id)
    if folio.status != "open":
        raise FolioNotOpenError(f"Folio {folio_id} is not open")
    await assert_business_date_not_locked(db, folio.establishment_id, folio.business_date)

    payment = Payment(
        id=uuid.uuid4(), folio_id=folio.id, mode=mode, montant=montant, reference=reference,
        encaisse_par=actor, business_date=folio.business_date,
    )
    db.add(payment)
    folio.total_payments = round(float(folio.total_payments) + float(montant), 2)
    folio.version += 1
    await db.commit()
    await db.refresh(payment)
    await publish_payment_added(
        str(payment.id), str(folio.id), str(folio.booking_id), payment.mode, float(payment.montant),
        str(folio.establishment_id), folio.business_date.isoformat(),
    )
    return payment


async def check_out(db: AsyncSession, establishment_id: uuid.UUID, booking_id: uuid.UUID, *, actor: uuid.UUID) -> dict:
    """Workflow G (spec §4.7, lignes 502-525)."""
    try:
        booking = await get_booking(str(booking_id))
    except ReservationClientError as exc:
        raise InvalidBookingStateError(f"Could not read booking {booking_id}: {exc}") from exc

    if booking["establishment_id"] != str(establishment_id):
        raise InvalidBookingStateError(f"Booking {booking_id} does not belong to establishment {establishment_id}")
    if booking["status"] != "status_checked_in":
        raise InvalidBookingStateError(f"Booking status {booking['status']!r} does not allow check-out")

    folios = await list_folios_for_booking(db, booking_id)
    folio_a = next((f for f in folios if f.type == "A" and f.status == "open"), None)
    if folio_a is None:
        raise FolioNotFoundError(f"No open Folio A for booking {booking_id}")
    final_balance = float(folio_a.balance)
    if round(final_balance, 2) != 0:
        raise FolioNotBalancedError(
            f"Folio A balance is {final_balance}, must be 0 to check out", balance=final_balance
        )

    now = datetime.now(timezone.utc)
    folio_a.status, folio_a.closed_at, folio_a.closed_by = "closed", now, actor

    folio_b = next((f for f in folios if f.type == "B" and f.status == "open"), None)
    if folio_b is not None:
        remaining = round(float(folio_b.balance), 2)
        if remaining != 0:
            # Folio B -> mode Débiteur obligatoire (spec ligne 516) : pas un
            # vrai encaissement, juste l'écriture comptable qui facture
            # l'agence/société via partner-service (hors-scope ici).
            db.add(
                Payment(
                    id=uuid.uuid4(), folio_id=folio_b.id, mode="Débiteur", montant=remaining,
                    reference="Auto-settled at check-out", encaisse_par=actor, business_date=folio_b.business_date,
                )
            )
            folio_b.total_payments = round(float(folio_b.total_payments) + remaining, 2)
        folio_b.status, folio_b.closed_at, folio_b.closed_by = "closed", now, actor

    await db.commit()

    await update_booking_status(str(booking_id), "status_checked_out")

    room = await housekeeping_client.get_room(booking["room_id"])
    customer = await get_customer(str(establishment_id), booking["customer_id"])
    await publish_booking_checked_out(
        str(booking_id), booking["room_id"], final_balance, str(establishment_id),
        guest_name=f"{customer['first_name']} {customer['last_name']}", room_number=room["numero"],
    )
    return {"booking_id": booking_id, "folio_ids": [f.id for f in ([folio_a] + ([folio_b] if folio_b else []))]}


# --------------------------------------------------------------- reports ---


async def get_daily_debits(db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type) -> dict:
    stmt = select(FolioCharge.montant_ttc).join(Folio).where(
        Folio.establishment_id == establishment_id, FolioCharge.business_date == business_date
    )
    amounts = (await db.scalars(stmt)).all()
    return {"business_date": business_date.isoformat(), "total_debits": round(sum(float(a) for a in amounts), 2)}


async def get_daily_credits(db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type) -> dict:
    stmt = select(Payment.montant).join(Folio).where(
        Folio.establishment_id == establishment_id, Payment.business_date == business_date
    )
    amounts = (await db.scalars(stmt)).all()
    return {"business_date": business_date.isoformat(), "total_credits": round(sum(float(a) for a in amounts), 2)}


async def get_daily_ca_detail(db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type) -> dict:
    """Rapport `ca_detaille_J.pdf` (night-audit-service, D12) — CA ventilé
    par poste comptable HT/TVA/TTC."""
    stmt = select(
        FolioCharge.poste_comptable,
        func.sum(FolioCharge.montant_ht),
        func.sum(FolioCharge.tva_amount),
        func.sum(FolioCharge.montant_ttc),
    ).join(Folio).where(
        Folio.establishment_id == establishment_id, FolioCharge.business_date == business_date
    ).group_by(FolioCharge.poste_comptable)
    rows = (await db.execute(stmt)).all()
    return {
        "business_date": business_date.isoformat(),
        "lines": [
            {
                "poste_comptable": poste, "montant_ht": round(float(ht), 2),
                "tva_amount": round(float(tva), 2), "montant_ttc": round(float(ttc), 2),
            }
            for poste, ht, tva, ttc in rows
        ],
    }


async def get_daily_encashments(db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type) -> dict:
    """Rapport `encaissements_J.pdf` (night-audit-service, D12) — main
    courante par mode de règlement."""
    stmt = select(Payment.mode, func.sum(Payment.montant)).join(Folio).where(
        Folio.establishment_id == establishment_id, Payment.business_date == business_date
    ).group_by(Payment.mode)
    rows = (await db.execute(stmt)).all()
    return {
        "business_date": business_date.isoformat(),
        "lines": [{"mode": mode, "total": round(float(total), 2)} for mode, total in rows],
    }


async def get_debtors(db: AsyncSession, establishment_id: uuid.UUID) -> list[dict]:
    """Rapport `debiteurs_J.pdf` (night-audit-service, D12) — soldes
    débiteurs (Folio B ouverts), pas borné à une business_date (spec ligne
    629 : "Soldes débiteurs (Folio B ouverts)", un solde débiteur reste
    ouvert au-delà du jour où il a été créé)."""
    stmt = select(Folio).where(
        Folio.establishment_id == establishment_id, Folio.type == "B", Folio.status == "open"
    )
    folios = (await db.scalars(stmt)).all()
    return [
        {"folio_id": str(f.id), "booking_id": str(f.booking_id), "balance": float(f.balance)}
        for f in folios if round(float(f.balance), 2) != 0
    ]


async def get_departures(db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type) -> dict:
    """Rapport `departs_attendus_J+1.pdf` (night-audit-service, D12) —
    chambres + soldes restants dus. Les Folio A n'ont pas la check_out_date
    (pas de duplication du planning réservation dans fo_db) : on résout au
    cas par cas via reservation-service (N+1 REST, acceptable au volume
    d'un seul établissement/jour)."""
    stmt = select(Folio).where(
        Folio.establishment_id == establishment_id, Folio.type == "A", Folio.status == "open"
    )
    folios = (await db.scalars(stmt)).all()
    departures = []
    for folio in folios:
        try:
            booking = await get_booking(str(folio.booking_id))
        except ReservationClientError:
            continue
        if booking["check_out_date"] == business_date.isoformat():
            departures.append(
                {"folio_id": str(folio.id), "booking_id": str(folio.booking_id), "balance": float(folio.balance)}
            )
    return {"business_date": business_date.isoformat(), "departures": departures}


async def get_discrepancy_report(db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type) -> list[dict]:
    stmt = select(Folio).where(Folio.establishment_id == establishment_id, Folio.business_date == business_date)
    folios = (await db.scalars(stmt)).all()
    return [
        {"folio_id": str(f.id), "booking_id": str(f.booking_id), "type": f.type, "balance": float(f.balance)}
        for f in folios if round(float(f.balance), 2) != 0
    ]


async def handle_audit_closed(db: AsyncSession, payload: dict) -> None:
    """Consumer `audit.closed` (D9) — verrouille la date métier. Sans
    night-audit-service (Sprint 5) pour publier cet événement, ce handler
    n'est déclenché qu'en test (smoke test, publication synthétique)."""
    establishment_id = uuid.UUID(payload["establishment_id"])
    business_date = date_type.fromisoformat(payload["business_date"])
    lock = await db.get(BusinessDateLock, (establishment_id, business_date))
    if lock is None:
        lock = BusinessDateLock(
            establishment_id=establishment_id, business_date=business_date, is_locked=True,
            locked_at=datetime.now(timezone.utc),
        )
        db.add(lock)
    else:
        lock.is_locked = True
        lock.locked_at = datetime.now(timezone.utc)
    await db.commit()
