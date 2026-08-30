from __future__ import annotations

import hashlib
import uuid
from datetime import date as date_type
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import pdf
from app.domain.exceptions import (
    AuditAlreadyClosedError,
    AuditTokenInvalidError,
    DiscrepancyError,
    NoActiveAuditError,
)
from app.domain.models import AuditRun, SystemState
from app.events.publisher import publish_audit_closed
from app.infrastructure import analytics_client, front_office_client, minio_client, notification_client, reservation_client
from app.infrastructure.redis_client import (
    cache_business_date,
    consume_audit_token,
    get_cached_business_date,
    store_audit_token,
)

DISCREPANCY_TOLERANCE = 0.01


async def _get_audit_run(db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type) -> AuditRun | None:
    stmt = select(AuditRun).where(AuditRun.establishment_id == establishment_id, AuditRun.business_date == business_date)
    return (await db.scalars(stmt)).first()


async def verify_pre_audit(
    db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type, *, actor: uuid.UUID
) -> dict:
    """Étape 1 (spec §4.9, Vérification Pré-Audit)."""
    est_str, date_str = str(establishment_id), business_date.isoformat()

    run = await _get_audit_run(db, establishment_id, business_date)
    if run is not None and run.status == "closed":
        raise AuditAlreadyClosedError(f"Business date {business_date} already closed for establishment {establishment_id}")
    if run is None:
        run = AuditRun(
            id=uuid.uuid4(), establishment_id=establishment_id, business_date=business_date, status="balancing",
        )
        db.add(run)
    else:
        run.status = "balancing"

    debits = await front_office_client.get_daily_debits(est_str, date_str)
    credits = await front_office_client.get_daily_credits(est_str, date_str)
    total_debits = float(debits["total_debits"])
    total_credits = float(credits["total_credits"])
    discrepancy = round(total_debits - total_credits, 2)

    run.total_debits = total_debits
    run.total_credits = total_credits
    run.discrepancy = discrepancy

    if abs(discrepancy) > DISCREPANCY_TOLERANCE:
        run.status = "error"
        await db.commit()
        for channel in ("email", "push"):
            await notification_client.send_notification(
                establishment_id=est_str, event_type="audit.discrepancy_detected", channel=channel,
                recipient_role="admin", subject="Écart Night Audit détecté",
                body=f"Écart de {discrepancy} MAD détecté pour le {date_str} (débits={total_debits}, crédits={total_credits}).",
            )
        raise DiscrepancyError(f"Discrepancy of {discrepancy} detected for {business_date}", discrepancy)

    run.status = "balanced"
    await db.commit()
    await db.refresh(run)

    token = uuid.uuid4().hex
    await store_audit_token(token, est_str)

    return {
        "token_audit": token, "total_debits": total_debits, "total_credits": total_credits,
        "discrepancy": discrepancy, "status": run.status,
    }


async def get_discrepancy_report(establishment_id: uuid.UUID, business_date: date_type) -> list[dict]:
    return await front_office_client.get_discrepancy_report(str(establishment_id), business_date.isoformat())


async def close_audit(
    db: AsyncSession, establishment_id: uuid.UUID, business_date: date_type, token: str, *, actor: uuid.UUID
) -> dict:
    """Étape 2 (spec §4.9, Clôture — action irréversible)."""
    resolved_establishment_id = await consume_audit_token(token)
    if resolved_establishment_id is None or resolved_establishment_id != str(establishment_id):
        raise AuditTokenInvalidError("Invalid, expired, or already-consumed audit token")

    run = await _get_audit_run(db, establishment_id, business_date)
    if run is None:
        raise NoActiveAuditError(f"No audit run found for {business_date} — call /verify first")
    if run.status == "closed":
        raise AuditAlreadyClosedError(f"Business date {business_date} already closed")
    if run.status != "balanced":
        raise NoActiveAuditError(f"Audit run status is {run.status!r}, expected 'balanced' — call /verify first")

    est_str = str(establishment_id)
    date_str = business_date.isoformat()
    next_date = business_date + timedelta(days=1)
    next_date_str = next_date.isoformat()

    ca_detail = await front_office_client.get_daily_ca_detail(est_str, date_str)
    encashments = await front_office_client.get_daily_encashments(est_str, date_str)
    debtors = await front_office_client.get_debtors(est_str)
    departures = await front_office_client.get_departures(est_str, next_date_str)
    arrivals = await reservation_client.get_arrivals(est_str, next_date_str)
    forecast = await analytics_client.get_occupancy_forecast(est_str, next_date_str)

    reports = {
        "ca_detaille_J.pdf": pdf.render_ca_detail(est_str, date_str, ca_detail),
        "encaissements_J.pdf": pdf.render_encashments(est_str, date_str, encashments),
        "debiteurs_J.pdf": pdf.render_debtors(est_str, date_str, debtors),
        "departs_attendus_J+1.pdf": pdf.render_departures(est_str, date_str, departures),
        "arrivees_prevues_J+1.pdf": pdf.render_arrivals(est_str, date_str, arrivals),
        "occupancy_forecast_J+1.pdf": pdf.render_occupancy_forecast(est_str, date_str, forecast),
    }

    report_urls: dict[str, str] = {}
    for filename in sorted(reports):
        report_urls[filename] = await minio_client.upload_report(est_str, date_str, filename, reports[filename])

    report_hash = hashlib.sha256(b"".join(reports[name] for name in sorted(reports))).hexdigest()

    now = datetime.now(timezone.utc)
    run.status = "closed"
    run.closed_by = actor
    run.closed_at = now
    run.report_urls = report_urls
    run.report_hash = report_hash
    run.completed_at = now

    state = await db.get(SystemState, establishment_id)
    if state is None:
        state = SystemState(establishment_id=establishment_id, business_date=next_date, last_audit_run_id=run.id)
        db.add(state)
    else:
        state.business_date = next_date
        state.last_audit_run_id = run.id
        state.updated_at = now

    await db.commit()

    await cache_business_date(est_str, next_date_str)
    await publish_audit_closed(est_str, date_str, report_hash)
    await notification_client.send_notification(
        establishment_id=est_str, event_type="audit.report_ready", channel="email", recipient_role="manager",
        subject=f"Rapports Night Audit — {date_str}", body=f"Les rapports de clôture du {date_str} sont disponibles.",
        payload={"establishment_id": est_str, "business_date": date_str, "report_filenames": sorted(reports)},
    )

    return {
        "business_date": date_str, "new_business_date": next_date_str, "report_hash": report_hash,
        "report_urls": report_urls,
    }


async def get_business_date(db: AsyncSession, establishment_id: uuid.UUID) -> str:
    est_str = str(establishment_id)
    cached = await get_cached_business_date(est_str)
    if cached:
        return cached

    state = await db.get(SystemState, establishment_id)
    business_date = state.business_date.isoformat() if state is not None else date_type.today().isoformat()
    await cache_business_date(est_str, business_date)
    return business_date
