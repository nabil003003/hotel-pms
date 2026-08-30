import uuid
from datetime import date as date_type

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, assert_path_establishment_access, get_current_user, get_db, require_roles
from app.domain.exceptions import AuditAlreadyClosedError, AuditTokenInvalidError, DiscrepancyError, NoActiveAuditError
from app.domain.services import close_audit, get_business_date, get_discrepancy_report, verify_pre_audit
from app.infrastructure import minio_client

from .schemas import BusinessDateOut, CloseIn, CloseOut, DiscrepancyItemOut, VerifyIn, VerifyOut

router = APIRouter(prefix="/api/v1/night-audit", tags=["night-audit"])

AUDIT_ROLES = ("manager", "admin")

# Whitelist des noms générés par close_audit (app/domain/services.py) — le nom
# vient de l'URL, jamais interprété comme un chemin MinIO arbitraire (pas de
# traversal possible via ../).
REPORT_FILENAMES = {
    "ca_detaille_J.pdf",
    "encaissements_J.pdf",
    "debiteurs_J.pdf",
    "departs_attendus_J+1.pdf",
    "arrivees_prevues_J+1.pdf",
    "occupancy_forecast_J+1.pdf",
}


@router.post("/verify", response_model=VerifyOut)
async def verify_endpoint(
    body: VerifyIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*AUDIT_ROLES)),
) -> VerifyOut:
    """Étape 1 (spec §4.9)."""
    assert_path_establishment_access(user, body.establishment_id)
    try:
        result = await verify_pre_audit(db, body.establishment_id, body.business_date, actor=uuid.UUID(user.sub))
    except AuditAlreadyClosedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, {"code": "ALREADY_CLOSED", "message": str(exc)}) from exc
    except DiscrepancyError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"code": "DISCREPANCY_DETECTED", "message": str(exc), "discrepancy": exc.discrepancy},
        ) from exc
    return VerifyOut.model_validate(result)


@router.get("/discrepancy-report", response_model=list[DiscrepancyItemOut])
async def discrepancy_report_endpoint(
    establishment_id: uuid.UUID,
    date: date_type,
    user: CurrentUser = Depends(require_roles(*AUDIT_ROLES)),
) -> list[DiscrepancyItemOut]:
    assert_path_establishment_access(user, establishment_id)
    result = await get_discrepancy_report(establishment_id, date)
    return [DiscrepancyItemOut.model_validate(r) for r in result]


@router.post("/close", response_model=CloseOut)
async def close_endpoint(
    body: CloseIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*AUDIT_ROLES)),
    x_audit_token: str | None = Header(None, alias="X-Audit-Token"),
) -> CloseOut:
    """Étape 2 (spec §4.9) — action irréversible."""
    assert_path_establishment_access(user, body.establishment_id)
    if not x_audit_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "X-Audit-Token header is required")
    try:
        result = await close_audit(
            db, body.establishment_id, body.business_date, x_audit_token, actor=uuid.UUID(user.sub)
        )
    except AuditTokenInvalidError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    except AuditAlreadyClosedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, {"code": "ALREADY_CLOSED", "message": str(exc)}) from exc
    except NoActiveAuditError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, {"code": "NO_ACTIVE_AUDIT", "message": str(exc)}) from exc
    return CloseOut.model_validate(result)


@router.get("/reports/{establishment_id}/{business_date}/{filename}")
async def download_report_endpoint(
    establishment_id: uuid.UUID,
    business_date: date_type,
    filename: str,
    user: CurrentUser = Depends(require_roles(*AUDIT_ROLES)),
) -> Response:
    assert_path_establishment_access(user, establishment_id)
    if filename not in REPORT_FILENAMES:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown report filename")
    try:
        data = await minio_client.get_report(str(establishment_id), business_date.isoformat(), filename)
    except ClientError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found") from exc
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/business-date", response_model=BusinessDateOut)
async def business_date_endpoint(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> BusinessDateOut:
    assert_path_establishment_access(user, establishment_id)
    business_date = await get_business_date(db, establishment_id)
    return BusinessDateOut(establishment_id=establishment_id, business_date=business_date)
