import json
import uuid
from datetime import date as date_type

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, assert_path_establishment_access, get_current_user, get_db, require_roles
from app.domain.exceptions import (
    BusinessDateLockedError,
    CatalogItemNotFoundError,
    FolioNotBalancedError,
    FolioNotFoundError,
    FolioNotOpenError,
    InvalidBookingStateError,
    RoomNotReadyError,
)
from app.domain.services import (
    add_charge,
    add_payment,
    check_in,
    check_out,
    get_daily_ca_detail,
    get_daily_credits,
    get_daily_debits,
    get_daily_encashments,
    get_debtors,
    get_departures,
    get_discrepancy_report,
    get_folio,
    list_folios_for_booking,
)
from app.infrastructure import redis_client as idem

from .schemas import (
    ChargeCreateIn,
    ChargeOut,
    CheckInIn,
    CheckInOut,
    CheckOutIn,
    CheckOutOut,
    DailyCaDetailOut,
    DailyCreditsOut,
    DailyDebitsOut,
    DailyEncashmentsOut,
    DebtorItemOut,
    DeparturesOut,
    DiscrepancyItemOut,
    FolioOut,
    PaymentCreateIn,
    PaymentOut,
)

router = APIRouter(prefix="/api/v1/folios", tags=["folios"])


async def _idempotent(x_idempotency_key: str | None, compute):
    """Idempotence "mandatory" sur check-in/check-out/charges (spec) — même
    principe que reservation-service, résultat JSON caché 24h dans Redis."""
    if x_idempotency_key:
        cached = await idem.get_idempotent_result(x_idempotency_key)
        if cached:
            return json.loads(cached)
    result = await compute()
    if x_idempotency_key:
        await idem.set_idempotent_result(x_idempotency_key, json.dumps(result, default=str))
    return result


@router.post("/check-in", response_model=CheckInOut, status_code=status.HTTP_201_CREATED)
async def check_in_endpoint(
    body: CheckInIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("receptionniste", "manager", "admin")),
    x_idempotency_key: str | None = Header(None, alias="X-Idempotency-Key"),
) -> CheckInOut:
    """Workflow D (spec §4.4)."""
    assert_path_establishment_access(user, body.establishment_id)

    async def _compute():
        try:
            result = await check_in(db, body.establishment_id, body.booking_id, actor=uuid.UUID(user.sub))
        except RoomNotReadyError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, {"code": "PRECONDITION_FAILED", "message": str(exc)}) from exc
        except InvalidBookingStateError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, {"code": "INVALID_BOOKING_STATE", "message": str(exc)}) from exc
        except BusinessDateLockedError as exc:
            raise HTTPException(status.HTTP_423_LOCKED, str(exc)) from exc
        return {"booking_id": str(result["booking_id"]), "folio_ids": [str(f) for f in result["folio_ids"]]}

    result = await _idempotent(x_idempotency_key, _compute)
    return CheckInOut.model_validate(result)


@router.get("/{folio_id}", response_model=FolioOut)
async def read_folio(
    folio_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> FolioOut:
    try:
        folio = await get_folio(db, folio_id)
    except FolioNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, folio.establishment_id)
    return FolioOut.model_validate(folio)


@router.get("", response_model=list[FolioOut])
async def read_folios_for_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[FolioOut]:
    folios = await list_folios_for_booking(db, booking_id)
    for folio in folios:
        assert_path_establishment_access(user, folio.establishment_id)
    return [FolioOut.model_validate(f) for f in folios]


@router.post("/{folio_id}/charges", response_model=ChargeOut, status_code=status.HTTP_201_CREATED)
async def add_charge_endpoint(
    folio_id: uuid.UUID,
    body: ChargeCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("receptionniste", "manager", "admin")),
    x_idempotency_key: str | None = Header(None, alias="X-Idempotency-Key"),
) -> ChargeOut:
    """Workflow E (spec §4.5)."""
    try:
        folio = await get_folio(db, folio_id)
    except FolioNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, folio.establishment_id)

    async def _compute():
        try:
            charge = await add_charge(
                db, folio_id, actor=uuid.UUID(user.sub), **body.model_dump()
            )
        except FolioNotOpenError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        except CatalogItemNotFoundError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        except BusinessDateLockedError as exc:
            raise HTTPException(status.HTTP_423_LOCKED, str(exc)) from exc
        return ChargeOut.model_validate(charge).model_dump(mode="json")

    result = await _idempotent(x_idempotency_key, _compute)
    return ChargeOut.model_validate(result)


@router.post("/{folio_id}/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
async def add_payment_endpoint(
    folio_id: uuid.UUID,
    body: PaymentCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("receptionniste", "manager", "admin")),
) -> PaymentOut:
    try:
        folio = await get_folio(db, folio_id)
    except FolioNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, folio.establishment_id)
    try:
        payment = await add_payment(db, folio_id, actor=uuid.UUID(user.sub), **body.model_dump())
    except FolioNotOpenError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except BusinessDateLockedError as exc:
        raise HTTPException(status.HTTP_423_LOCKED, str(exc)) from exc
    return PaymentOut.model_validate(payment)


@router.post("/check-out", response_model=CheckOutOut)
async def check_out_endpoint(
    body: CheckOutIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("receptionniste", "manager", "admin")),
    x_idempotency_key: str | None = Header(None, alias="X-Idempotency-Key"),
) -> CheckOutOut:
    """Workflow G (spec §4.7)."""
    assert_path_establishment_access(user, body.establishment_id)

    async def _compute():
        try:
            result = await check_out(db, body.establishment_id, body.booking_id, actor=uuid.UUID(user.sub))
        except FolioNotBalancedError as exc:
            raise HTTPException(
                status.HTTP_409_CONFLICT, {"code": "FOLIO_NOT_BALANCED", "message": str(exc), "balance": float(exc.balance)}
            ) from exc
        except InvalidBookingStateError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, {"code": "INVALID_BOOKING_STATE", "message": str(exc)}) from exc
        except FolioNotFoundError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        return {"booking_id": str(result["booking_id"]), "folio_ids": [str(f) for f in result["folio_ids"]]}

    result = await _idempotent(x_idempotency_key, _compute)
    return CheckOutOut.model_validate(result)


@router.post("/{folio_id}/reopen")
async def reopen_folio_endpoint(
    folio_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
) -> None:
    """Spec : toujours 403, aucun contournement de rôle documenté — pas
    même admin/super-admin."""
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Reopening a folio is permanently forbidden")


@router.get("/reports/daily-debits", response_model=DailyDebitsOut)
async def read_daily_debits(
    establishment_id: uuid.UUID,
    date: date_type,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("comptable", "manager", "admin")),
) -> DailyDebitsOut:
    assert_path_establishment_access(user, establishment_id)
    result = await get_daily_debits(db, establishment_id, date)
    return DailyDebitsOut.model_validate(result)


@router.get("/reports/daily-credits", response_model=DailyCreditsOut)
async def read_daily_credits(
    establishment_id: uuid.UUID,
    date: date_type,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("comptable", "manager", "admin")),
) -> DailyCreditsOut:
    assert_path_establishment_access(user, establishment_id)
    result = await get_daily_credits(db, establishment_id, date)
    return DailyCreditsOut.model_validate(result)


@router.get("/reports/daily-ca-detail", response_model=DailyCaDetailOut)
async def read_daily_ca_detail(
    establishment_id: uuid.UUID,
    date: date_type,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("comptable", "manager", "admin")),
) -> DailyCaDetailOut:
    assert_path_establishment_access(user, establishment_id)
    result = await get_daily_ca_detail(db, establishment_id, date)
    return DailyCaDetailOut.model_validate(result)


@router.get("/reports/daily-encashments", response_model=DailyEncashmentsOut)
async def read_daily_encashments(
    establishment_id: uuid.UUID,
    date: date_type,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("comptable", "manager", "admin")),
) -> DailyEncashmentsOut:
    assert_path_establishment_access(user, establishment_id)
    result = await get_daily_encashments(db, establishment_id, date)
    return DailyEncashmentsOut.model_validate(result)


@router.get("/reports/debtors", response_model=list[DebtorItemOut])
async def read_debtors(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("comptable", "manager", "admin")),
) -> list[DebtorItemOut]:
    assert_path_establishment_access(user, establishment_id)
    result = await get_debtors(db, establishment_id)
    return [DebtorItemOut.model_validate(r) for r in result]


@router.get("/reports/departures", response_model=DeparturesOut)
async def read_departures(
    establishment_id: uuid.UUID,
    date: date_type,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("comptable", "manager", "admin")),
) -> DeparturesOut:
    assert_path_establishment_access(user, establishment_id)
    result = await get_departures(db, establishment_id, date)
    return DeparturesOut.model_validate(result)


@router.get("/reports/discrepancy", response_model=list[DiscrepancyItemOut])
async def read_discrepancy_report(
    establishment_id: uuid.UUID,
    date: date_type,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("comptable", "manager", "admin")),
) -> list[DiscrepancyItemOut]:
    assert_path_establishment_access(user, establishment_id)
    result = await get_discrepancy_report(db, establishment_id, date)
    return [DiscrepancyItemOut.model_validate(r) for r in result]
