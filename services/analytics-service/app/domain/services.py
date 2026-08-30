from __future__ import annotations

import uuid
from datetime import date as date_type
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import InvalidPeriodError
from app.domain.models import ChannelPerformance, DailyKpiSnapshot, MonthlyKpiAggregation
from app.infrastructure import establishment_client, night_audit_client
from app.infrastructure import redis_client as cache
from app.infrastructure.reservation_client import get_arrivals_count, get_booking, get_market_segments, get_occupied_room_count

# Dupliqué de front-office-service (D2 — pas de lib partagée) : nécessaire
# pour reconstituer HT/TVA depuis le montant TTC porté par `folio.charge_added`
# (l'événement ne transporte pas le détail de la TVA).
POSTE_TVA_RATES: dict[str, float] = {
    "HEB": 10, "PDJ": 10, "RES": 10, "DIN": 10,
    "BAR": 20, "SPA": 20, "ACT": 20, "HAM": 20, "TRF": 20, "EXC": 20,
    "TS": 0, "TPT": 0, "REM": 0,
}


async def _invalidate_kpi_cache(establishment_id: uuid.UUID, business_date: date_type) -> None:
    """`kpi/today`/`kpi/monthly` sont cachés (Redis, 5 min / 1h — Workflow J,
    spec lignes 667/675) pour éviter de recalculer à chaque lecture. Mais un
    TTL fixe comme SEULE voie de rafraîchissement fait qu'un check-in/charge/
    paiement reste invisible jusqu'à expiration — invalider activement au
    moment de l'écriture rend la lecture suivante immédiate, le TTL restant
    un filet de sécurité (au cas où un événement serait perdu) plutôt que le
    mécanisme de fraîcheur principal."""
    await cache.cache_delete(f"kpi:today:{establishment_id}")
    await cache.cache_delete(f"kpi:monthly:{establishment_id}:{business_date.year:04d}-{business_date.month:02d}")


def _month_range(year: int, month: int) -> tuple[date_type, date_type]:
    if not (1 <= month <= 12):
        raise InvalidPeriodError(f"Invalid month: {month}")
    start = date_type(year, month, 1)
    end = date_type(year + 1, 1, 1) if month == 12 else date_type(year, month + 1, 1)
    return start, end


def _parse_period(period: str) -> tuple[int, int]:
    try:
        year_str, month_str = period.split("-")
        return int(year_str), int(month_str)
    except (ValueError, AttributeError) as exc:
        raise InvalidPeriodError(f"Invalid period {period!r}, expected YYYY-MM") from exc


# --------------------------------------------------------- event handlers --


async def _get_or_create_snapshot(
    db: AsyncSession, business_date: date_type, establishment_id: uuid.UUID, segment_id: uuid.UUID
) -> DailyKpiSnapshot:
    # `booking_events` et `folio_events` sont deux consumers RabbitMQ
    # indépendants (asyncio.gather, app/events/consumer.py) qui peuvent tous
    # les deux déclencher la création du même snapshot (même business_date/
    # establishment_id/segment_id) au même instant — un simple check-then-
    # insert (db.get() puis db.add()) laissait passer un
    # UniqueViolationError sur daily_kpi_snapshot_pkey quand les deux
    # gagnaient la course. INSERT ... ON CONFLICT DO NOTHING rend la
    # création atomique ; SELECT ... FOR UPDATE sérialise ensuite le
    # cycle lecture-incrément-commit contre tout autre handler concurrent
    # sur la même ligne.
    insert_stmt = pg_insert(DailyKpiSnapshot).values(
        business_date=business_date, establishment_id=establishment_id, segment_id=segment_id,
        nuitees=0, ca_brut=0, ca_ht=0, tva_total=0, to_pct=0, adr=0, revpar=0, dms=0, pax_total=0,
    ).on_conflict_do_nothing(
        index_elements=["business_date", "establishment_id", "segment_id"]
    )
    await db.execute(insert_stmt)
    row = (
        await db.execute(
            select(DailyKpiSnapshot)
            .where(
                DailyKpiSnapshot.business_date == business_date,
                DailyKpiSnapshot.establishment_id == establishment_id,
                DailyKpiSnapshot.segment_id == segment_id,
            )
            .with_for_update()
        )
    ).scalar_one()
    return row


async def _recompute_ratios(row: DailyKpiSnapshot, establishment_id: uuid.UUID) -> None:
    """`dms` n'est pas calculée en Sprint 4 (nécessite un comptage de séjours
    distincts que ce sprint ne tient pas — voir D10) : reste à sa valeur
    par défaut (0), pas de chiffre fabriqué."""
    total_rooms = await establishment_client.get_total_rooms(str(establishment_id))
    nuitees = int(row.nuitees)
    ca_ht = float(row.ca_ht)
    if total_rooms:
        row.to_pct = round(min(100.0, (nuitees / total_rooms) * 100), 2)
        row.revpar = round(ca_ht / total_rooms, 2)
    if nuitees:
        row.adr = round(ca_ht / nuitees, 2)


async def handle_booking_checked_in(db: AsyncSession, payload: dict) -> None:
    """`nuitees`/`pax_total` incrémentés du nombre de nuits/pax du séjour qui
    démarre — proxy simplifié (D10), pas le comptage nuit-par-nuit précis
    qu'une vraie clôture journalière (night-audit-service, Sprint 5) ferait."""
    booking = await get_booking(payload["booking_id"])
    if booking is None:
        return
    establishment_id = uuid.UUID(booking["establishment_id"])
    segment_id = uuid.UUID(booking["market_segment_id"])
    check_in_date = date_type.fromisoformat(booking["check_in_date"])
    check_out_date = date_type.fromisoformat(booking["check_out_date"])
    nights = (check_out_date - check_in_date).days
    pax = int(booking["adults"]) + int(booking["children"])

    # Date métier du payload (front-office-service la connaît déjà via
    # night-audit-service au moment du check-in), pas `date.today()` : une
    # clôture avance `business_date` au-delà du calendrier, et `kpi/today`
    # lit désormais avec la même date métier (cf. `get_kpi_today`) — utiliser
    # `date.today()` ici désynchroniserait silencieusement écriture/lecture.
    business_date = date_type.fromisoformat(payload["business_date"])
    row = await _get_or_create_snapshot(db, business_date, establishment_id, segment_id)
    row.nuitees = int(row.nuitees) + nights
    row.pax_total = int(row.pax_total) + pax
    await _recompute_ratios(row, establishment_id)
    await db.commit()
    await _invalidate_kpi_cache(establishment_id, business_date)


async def handle_folio_charge_added(db: AsyncSession, payload: dict) -> None:
    booking = await get_booking(payload["booking_id"])
    if booking is None:
        return
    establishment_id = uuid.UUID(payload["establishment_id"])
    segment_id = uuid.UUID(booking["market_segment_id"])
    amount_ttc = float(payload["amount"])
    tva_rate = POSTE_TVA_RATES.get(payload["poste"], 0)
    amount_ht = round(amount_ttc / (1 + tva_rate / 100), 2)
    tva_amount = round(amount_ttc - amount_ht, 2)

    business_date = date_type.fromisoformat(payload["business_date"])
    row = await _get_or_create_snapshot(db, business_date, establishment_id, segment_id)
    row.ca_brut = round(float(row.ca_brut) + amount_ttc, 2)
    row.ca_ht = round(float(row.ca_ht) + amount_ht, 2)
    row.tva_total = round(float(row.tva_total) + tva_amount, 2)
    await _recompute_ratios(row, establishment_id)
    await db.commit()
    await _invalidate_kpi_cache(establishment_id, business_date)


async def handle_payment_added(db: AsyncSession, payload: dict) -> None:
    """`folio.payment_added` — jusqu'ici jamais publié par front-office-service
    (cf. `publish_payment_added`), donc un encaissement n'avait aucun effet
    visible ici : ni consumer, ni colonne. `encaissements` est délibérément
    distinct de `ca_brut` (alimenté par les charges, pas les paiements) —
    le CA reste comptabilisé à la facturation, l'encaissement au recouvrement
    réel, comme au front-office (`fetchDailyCredits`/`fetchDailyEncashments`)."""
    booking = await get_booking(payload["booking_id"])
    if booking is None:
        return
    establishment_id = uuid.UUID(payload["establishment_id"])
    segment_id = uuid.UUID(booking["market_segment_id"])
    business_date = date_type.fromisoformat(payload["business_date"])

    row = await _get_or_create_snapshot(db, business_date, establishment_id, segment_id)
    row.encaissements = round(float(row.encaissements) + float(payload["montant"]), 2)
    await db.commit()
    await _invalidate_kpi_cache(establishment_id, business_date)


async def handle_channel_booking_received(db: AsyncSession, payload: dict) -> None:
    internal_booking_id = payload.get("internal_booking_id")
    if not internal_booking_id:
        return  # ancien format d'événement (avant Sprint 3/D6) sans booking réel — rien à agréger
    booking = await get_booking(internal_booking_id)
    if booking is None:
        return
    establishment_id = uuid.UUID(payload["establishment_id"])
    channel = payload["ota_name"]
    today = date_type.today()

    row = await db.get(ChannelPerformance, (today, establishment_id, channel))
    if row is None:
        row = ChannelPerformance(
            business_date=today, establishment_id=establishment_id, channel=channel,
            bookings_count=0, revenue=0, commission=0, net_revenue=0,
        )
        db.add(row)
    revenue = float(booking.get("total_amount") or 0)
    row.bookings_count = int(row.bookings_count) + 1
    row.revenue = round(float(row.revenue) + revenue, 2)
    # commission : pas de source fiable au moment de l'événement
    # (partner_rates.commission_pct est lié à des combinaisons saison/catégorie,
    # pas une valeur unique par réservation) — reste à 0, non fabriqué (D10).
    row.net_revenue = round(float(row.revenue) - float(row.commission), 2)
    await db.commit()


async def handle_audit_closed(db: AsyncSession, payload: dict) -> None:
    """`audit.closed` (night-audit-service, Sprint 5, pas encore construit) :
    déclenche une re-consolidation de l'agrégat mensuel pour le mois de la
    date clôturée plutôt que de fabriquer une notion de "snapshot figé"
    supplémentaire — les compteurs journaliers sont déjà tenus à jour en
    temps réel (D10)."""
    establishment_id = uuid.UUID(payload["establishment_id"])
    business_date = date_type.fromisoformat(payload["business_date"])
    await recompute_monthly_aggregation(db, establishment_id, business_date.year, business_date.month)


# ------------------------------------------------------------------ reads --


async def recompute_monthly_aggregation(db: AsyncSession, establishment_id: uuid.UUID, year: int, month: int) -> None:
    """Pas de Celery (D10) : recalculée à la demande depuis `daily_kpi_snapshot`
    plutôt que via un job planifié — toujours juste, coût négligeable."""
    start, end = _month_range(year, month)
    stmt = select(DailyKpiSnapshot).where(
        DailyKpiSnapshot.establishment_id == establishment_id,
        DailyKpiSnapshot.business_date >= start,
        DailyKpiSnapshot.business_date < end,
    )
    rows = (await db.scalars(stmt)).all()

    by_segment: dict[uuid.UUID, dict] = {}
    for r in rows:
        acc = by_segment.setdefault(r.segment_id, {"nuitees": 0, "ca_brut": 0.0})
        acc["nuitees"] += int(r.nuitees)
        acc["ca_brut"] += float(r.ca_brut)

    total_rooms = await establishment_client.get_total_rooms(str(establishment_id))
    days_in_month = (end - start).days

    for segment_id, acc in by_segment.items():
        agg = await db.get(MonthlyKpiAggregation, (year, month, establishment_id, segment_id))
        if agg is None:
            agg = MonthlyKpiAggregation(year=year, month=month, establishment_id=establishment_id, segment_id=segment_id)
            db.add(agg)
        agg.nuitees = acc["nuitees"]
        agg.ca_brut = round(acc["ca_brut"], 2)
        if total_rooms:
            agg.to_pct = round(min(100.0, (acc["nuitees"] / (total_rooms * days_in_month)) * 100), 2)
            agg.revpar = round(acc["ca_brut"] / (total_rooms * days_in_month), 2)
        if acc["nuitees"]:
            agg.adr = round(acc["ca_brut"] / acc["nuitees"], 2)
    await db.commit()


async def get_kpi_today(db: AsyncSession, establishment_id: uuid.UUID) -> dict:
    # Date métier réelle (night-audit), pas `date.today()` : les écritures
    # (`handle_booking_checked_in`/`handle_folio_charge_added`/
    # `handle_payment_added`) sont indexées sur `business_date`, qui peut être
    # en avance sur le calendrier après une clôture — lire avec le calendrier
    # ferait chercher le snapshot de la mauvaise journée (silencieusement
    # vide), ce qui donnait l'impression que rien ne "bougeait" ici.
    today = await night_audit_client.get_business_date(str(establishment_id))
    stmt = select(DailyKpiSnapshot).where(
        DailyKpiSnapshot.establishment_id == establishment_id, DailyKpiSnapshot.business_date == today
    )
    rows = (await db.scalars(stmt)).all()

    nuitees = sum(int(r.nuitees) for r in rows)
    ca_ht = sum(float(r.ca_ht) for r in rows)
    ca_total = sum(float(r.ca_brut) for r in rows)
    encaissements_total = sum(float(r.encaissements) for r in rows)
    total_rooms = await establishment_client.get_total_rooms(str(establishment_id))
    # Occupation réelle à l'instant T (chambres avec un séjour status_checked_in
    # actuellement), pas `nuitees` : ce compteur est cumulatif depuis le début
    # de la journée métier et n'est jamais décrémenté au check-out — un séjour
    # d'une nuit déjà reparti restait compté comme occupé jusqu'à la clôture.
    occupied_rooms = await get_occupied_room_count(str(establishment_id))
    occupancy_rate = round(min(100.0, (occupied_rooms / total_rooms) * 100), 2) if total_rooms else 0.0
    adr = round(ca_ht / nuitees, 2) if nuitees else 0.0
    revpar = round(ca_ht / total_rooms, 2) if total_rooms else 0.0

    return {
        "establishment_id": establishment_id, "occupancy_rate": occupancy_rate, "adr": adr, "revpar": revpar,
        "ca_total": round(ca_total, 2), "encaissements_total": round(encaissements_total, 2),
        "compare_n1": None, "compare_last_month": None,
    }


async def get_kpi_monthly(db: AsyncSession, establishment_id: uuid.UUID, year: int, month: int) -> dict:
    await recompute_monthly_aggregation(db, establishment_id, year, month)
    start, end = _month_range(year, month)
    stmt = select(MonthlyKpiAggregation).where(
        MonthlyKpiAggregation.establishment_id == establishment_id,
        MonthlyKpiAggregation.year == year, MonthlyKpiAggregation.month == month,
    )
    rows = (await db.scalars(stmt)).all()

    nuitees = sum(int(r.nuitees) for r in rows)
    ca_brut = sum(float(r.ca_brut) for r in rows)
    total_rooms = await establishment_client.get_total_rooms(str(establishment_id))
    days_in_month = (end - start).days
    occupancy_rate = round(min(100.0, (nuitees / (total_rooms * days_in_month)) * 100), 2) if total_rooms else 0.0
    adr = round(ca_brut / nuitees, 2) if nuitees else 0.0
    revpar = round(ca_brut / (total_rooms * days_in_month), 2) if total_rooms else 0.0

    return {
        "establishment_id": establishment_id, "period": f"{year:04d}-{month:02d}", "occupancy_rate": occupancy_rate,
        "adr": adr, "revpar": revpar, "dms": 0.0, "ca_total": round(ca_brut, 2), "compare_n1": None,
    }


async def get_kpi_consolidated(db: AsyncSession, year: int, month: int) -> dict:
    stmt = select(MonthlyKpiAggregation).where(
        MonthlyKpiAggregation.year == year, MonthlyKpiAggregation.month == month
    )
    rows = (await db.scalars(stmt)).all()
    nuitees = sum(int(r.nuitees) for r in rows)
    ca_brut = sum(float(r.ca_brut) for r in rows)
    return {"period": f"{year:04d}-{month:02d}", "nuitees": nuitees, "ca_total": round(ca_brut, 2)}


async def get_segments_distribution(db: AsyncSession, establishment_id: uuid.UUID, period: str) -> dict:
    year, month = _parse_period(period)
    await recompute_monthly_aggregation(db, establishment_id, year, month)
    stmt = select(MonthlyKpiAggregation).where(
        MonthlyKpiAggregation.establishment_id == establishment_id,
        MonthlyKpiAggregation.year == year, MonthlyKpiAggregation.month == month,
    )
    rows = (await db.scalars(stmt)).all()
    labels = {s["id"]: s["label"] for s in await get_market_segments(str(establishment_id))}
    total_nuitees = sum(int(r.nuitees) for r in rows) or 1

    return {
        "segments": [
            {
                "segment_id": str(r.segment_id), "label": labels.get(str(r.segment_id), "?"),
                "nuitees": int(r.nuitees), "pct_volume": round(int(r.nuitees) / total_nuitees * 100, 2),
            }
            for r in rows
        ]
    }


async def get_segments_revenue(db: AsyncSession, establishment_id: uuid.UUID, period: str) -> dict:
    year, month = _parse_period(period)
    await recompute_monthly_aggregation(db, establishment_id, year, month)
    stmt = select(MonthlyKpiAggregation).where(
        MonthlyKpiAggregation.establishment_id == establishment_id,
        MonthlyKpiAggregation.year == year, MonthlyKpiAggregation.month == month,
    )
    rows = (await db.scalars(stmt)).all()
    labels = {s["id"]: s["label"] for s in await get_market_segments(str(establishment_id))}

    return {
        "segments": [
            {"segment_id": str(r.segment_id), "label": labels.get(str(r.segment_id), "?"), "ca_brut": round(float(r.ca_brut), 2)}
            for r in rows
        ]
    }


async def get_segments_trend(
    db: AsyncSession, establishment_id: uuid.UUID, segment_code: str, months_back: int = 6
) -> dict:
    segments = await get_market_segments(str(establishment_id))
    segment = next((s for s in segments if s["code"] == segment_code), None)
    if segment is None:
        return {"data": []}
    segment_id = uuid.UUID(segment["id"])

    today = date_type.today()
    data = []
    year, month = today.year, today.month
    for _ in range(months_back):
        await recompute_monthly_aggregation(db, establishment_id, year, month)
        agg = await db.get(MonthlyKpiAggregation, (year, month, establishment_id, segment_id))
        data.append({
            "period": f"{year:04d}-{month:02d}",
            "to": float(agg.to_pct) if agg else 0.0,
            "adr": float(agg.adr) if agg else 0.0,
            "revpar": float(agg.revpar) if agg else 0.0,
        })
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    data.reverse()
    return {"data": data}


async def get_ytd_compare(db: AsyncSession, establishment_id: uuid.UUID, year: int, month: int) -> dict:
    await recompute_monthly_aggregation(db, establishment_id, year, month)
    await recompute_monthly_aggregation(db, establishment_id, year - 1, month)

    async def _totals(y: int) -> dict:
        stmt = select(MonthlyKpiAggregation).where(
            MonthlyKpiAggregation.establishment_id == establishment_id,
            MonthlyKpiAggregation.year == y, MonthlyKpiAggregation.month == month,
        )
        rows = (await db.scalars(stmt)).all()
        nuitees = sum(int(r.nuitees) for r in rows)
        ca = sum(float(r.ca_brut) for r in rows)
        to_pct = rows[0].to_pct if len(rows) == 1 else 0
        adr = round(ca / nuitees, 2) if nuitees else 0.0
        return {"to": float(to_pct or 0), "adr": adr, "ca": round(ca, 2)}

    current, previous = await _totals(year), await _totals(year - 1)

    def _delta(cur: float, prev: float) -> float:
        return round(((cur - prev) / prev) * 100, 2) if prev else 0.0

    return {
        "current_year": current, "previous_year": previous,
        "deltas": {
            "to_pct": _delta(current["to"], previous["to"]), "adr_pct": _delta(current["adr"], previous["adr"]),
            "ca_pct": _delta(current["ca"], previous["ca"]),
        },
    }


async def get_channel_performance(db: AsyncSession, establishment_id: uuid.UUID, period: str) -> dict:
    """Vue "revenu par canal" propre à analytics-service (`channel_performance`,
    alimentée par `channel.booking_received`) — distincte de l'endpoint
    `/api/v1/channel/performance` de channel-manager-service (Sprint 2,
    santé de synchronisation via `sync_logs`) : même forme de chemin, même
    intention documentée dans les deux README, mais services/ports différents."""
    year, month = _parse_period(period)
    start, end = _month_range(year, month)
    stmt = select(ChannelPerformance).where(
        ChannelPerformance.establishment_id == establishment_id,
        ChannelPerformance.business_date >= start, ChannelPerformance.business_date < end,
    )
    rows = (await db.scalars(stmt)).all()

    by_channel: dict[str, dict] = {}
    for r in rows:
        acc = by_channel.setdefault(r.channel, {"bookings_count": 0, "revenue": 0.0, "commission": 0.0, "net_revenue": 0.0})
        acc["bookings_count"] += int(r.bookings_count)
        acc["revenue"] += float(r.revenue)
        acc["commission"] += float(r.commission)
        acc["net_revenue"] += float(r.net_revenue)

    return {"channels": [{"channel": ch, **vals} for ch, vals in by_channel.items()]}


async def get_occupancy_forecast(db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type) -> dict:
    """Rapport `occupancy_forecast_J+1.pdf` (night-audit-service, D12) —
    pas un vrai moteur de prévision : arrivées connues à `business_date`
    (reservation-service) ÷ capacité, ADR/RevPAR proxy = moyenne des 7
    derniers jours de `daily_kpi_snapshot`. Approximation documentée, pas un
    chiffre contractuel."""
    total_rooms = await establishment_client.get_total_rooms(str(establishment_id))
    arrivals = await get_arrivals_count(str(establishment_id), business_date.isoformat())
    projected_occupancy_rate = round(min(100.0, (arrivals / total_rooms) * 100), 2) if total_rooms else 0.0

    week_ago = business_date - timedelta(days=7)
    stmt = select(
        func.sum(DailyKpiSnapshot.ca_ht), func.sum(DailyKpiSnapshot.nuitees)
    ).where(
        DailyKpiSnapshot.establishment_id == establishment_id,
        DailyKpiSnapshot.business_date >= week_ago, DailyKpiSnapshot.business_date < business_date,
    )
    ca_ht_sum, nuitees_sum = (await db.execute(stmt)).one()
    adr_proxy = round(float(ca_ht_sum) / int(nuitees_sum), 2) if ca_ht_sum and nuitees_sum else 0.0
    revpar_proxy = round(adr_proxy * projected_occupancy_rate / 100, 2)

    return {
        "establishment_id": establishment_id, "business_date": business_date.isoformat(),
        "arrivals_count": arrivals, "projected_occupancy_rate": projected_occupancy_rate,
        "adr_proxy": adr_proxy, "revpar_proxy": revpar_proxy,
    }
