import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    CurrentUser,
    assert_path_establishment_access,
    get_current_user,
    get_db,
    require_roles,
)
from app.domain.exceptions import (
    InvalidWebhookSignatureError,
    OtaConflictError,
    OtaMappingNotFoundError,
)
from app.domain.services import create_or_update_connection, get_performance, list_connections, process_webhook

from .schemas import (
    ChannelConnectionCreateIn,
    ChannelConnectionOut,
    PerformanceOut,
    WebhookBookingIn,
    WebhookResponseOut,
)

router = APIRouter(prefix="/api/v1/channel", tags=["channel"])

# ------------------------------------------------------------- connections --


@router.post(
    "/connections/{establishment_id}", response_model=ChannelConnectionOut, status_code=status.HTTP_201_CREATED
)
async def upsert_connection(
    establishment_id: uuid.UUID,
    body: ChannelConnectionCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("manager", "admin")),
) -> ChannelConnectionOut:
    """Workflow K étape 5 (spec ligne 741) — le manager est explicitement
    autorisé à gérer le Channel Manager (§3.3), contrairement aux tarifs."""
    assert_path_establishment_access(user, establishment_id)
    connection = await create_or_update_connection(db, establishment_id, **body.model_dump())
    return ChannelConnectionOut.model_validate(connection)


@router.get("/connections/{establishment_id}", response_model=list[ChannelConnectionOut])
async def read_connections(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[ChannelConnectionOut]:
    assert_path_establishment_access(user, establishment_id)
    connections = await list_connections(db, establishment_id)
    return [ChannelConnectionOut.model_validate(c) for c in connections]


# ------------------------------------------------------------------ webhook -


@router.post("/webhook/{ota_name}", response_model=WebhookResponseOut, status_code=status.HTTP_200_OK)
async def webhook(
    ota_name: str,
    body: WebhookBookingIn,
    establishment_id: uuid.UUID,
    request: Request,
    x_ota_signature: str = Header(..., alias="X-OTA-Signature"),
    x_correlation_id: str | None = Header(None, alias="X-Correlation-Id"),
    db: AsyncSession = Depends(get_db),
) -> WebhookResponseOut:
    """Workflow C (spec ligne 288-321). Pas de JWT — l'appelant est l'OTA
    externe, authentifiée par signature HMAC (`X-OTA-Signature`) plutôt que
    par bearer token. `establishment_id` en query param : simplification
    Sprint 2 (une vraie intégration OTA distinguerait les établissements par
    URL/token de connexion dédié — hors scope tant qu'aucun credential OTA
    réel n'existe, voir plan Sprint 2 non-goals).

    Sprint 3 (D6) : crée réellement la réservation via un appel synchrone à
    reservation-service — `200 {internal_booking_id, status}`, contrat
    d'origine du spec."""
    raw_body = await request.body()
    correlation_id = x_correlation_id or str(uuid.uuid4())
    try:
        result = await process_webhook(
            db, establishment_id, ota_name, raw_body=raw_body, signature=x_ota_signature,
            correlation_id=correlation_id, payload=body.model_dump(),
        )
    except InvalidWebhookSignatureError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    except OtaConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, {"code": "OTA_CONFLICT", "message": str(exc)}) from exc
    except OtaMappingNotFoundError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, {"code": "MAPPING_ERROR", "message": str(exc)}
        ) from exc
    return WebhookResponseOut.model_validate(result)


# --------------------------------------------------------------- performance -


@router.get("/performance", response_model=PerformanceOut)
async def read_performance(
    establishment_id: uuid.UUID,
    period: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("manager", "admin")),
) -> PerformanceOut:
    """Spec ligne 709 — lu par analytics-service, format `period=YYYY-MM`."""
    assert_path_establishment_access(user, establishment_id)
    result = await get_performance(db, establishment_id, period)
    return PerformanceOut.model_validate(result)
