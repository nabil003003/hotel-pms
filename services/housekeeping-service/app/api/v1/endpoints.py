import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    CurrentUser,
    assert_path_establishment_access,
    get_current_user,
    get_db,
    require_roles,
    require_super_admin,
)
from app.domain.exceptions import InvalidTransitionError, ReasonRequiredError, RoomNotFoundError
from app.domain.models import ROOM_STATUSES
from app.domain.services import (
    change_room_status,
    create_incident,
    get_room,
    is_unblock_allowed,
    list_incidents,
    list_rooms,
    list_status_history,
    resync_from_establishment,
)
from app.infrastructure.keycloak import TokenValidationError, decode_access_token
from app.infrastructure.redis_client import subscribe_ws_channel

from .schemas import (
    IncidentCreateIn,
    IncidentOut,
    ResyncOut,
    RoomOut,
    RoomStatusOut,
    StatusChangeIn,
    StatusHistoryOut,
)

router = APIRouter(prefix="/api/v1", tags=["housekeeping"])

HOUSEKEEPING_ROLES = ("femme_de_chambre", "gouvernante", "manager", "admin")


@router.get("/rooms", response_model=list[RoomOut])
async def read_rooms(
    establishment_id: uuid.UUID,
    statut: str | None = None,
    floor: int | None = None,
    categorie: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[RoomOut]:
    assert_path_establishment_access(user, establishment_id)
    rooms = await list_rooms(db, establishment_id, statut=statut, floor=floor, categorie=categorie)
    return [RoomOut.model_validate(r) for r in rooms]


@router.get("/rooms/{room_id}", response_model=RoomOut)
async def read_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> RoomOut:
    try:
        room = await get_room(db, room_id)
    except RoomNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, room.establishment_id)
    return RoomOut.model_validate(room)


@router.get("/rooms/{room_id}/status", response_model=RoomStatusOut)
async def read_room_status(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> RoomStatusOut:
    """Utilisé en synchrone par front-office-service au check-in (Workflow D,
    Sprint 4) pour vérifier que la chambre est Propre/Contrôlée."""
    try:
        room = await get_room(db, room_id)
    except RoomNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, room.establishment_id)
    return RoomStatusOut(room_id=room.id, statut=room.statut)


@router.patch("/rooms/{room_id}/status", response_model=RoomOut)
async def patch_room_status(
    room_id: uuid.UUID,
    body: StatusChangeIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*HOUSEKEEPING_ROLES)),
) -> RoomOut:
    if body.new_status not in ROOM_STATUSES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown status: {body.new_status}")

    try:
        room = await get_room(db, room_id)
    except RoomNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, room.establishment_id)

    if room.statut == "Bloquée" and body.new_status == "Propre":
        if not is_unblock_allowed(user.roles, user.is_super_admin):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Déblocage réservé à gouvernante/manager/admin")

    try:
        updated = await change_room_status(
            db, room_id, new_status=body.new_status, reason=body.reason, changed_by=uuid.UUID(user.sub)
        )
    except InvalidTransitionError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={"code": "INVALID_TRANSITION", "allowed": exc.allowed},
        ) from exc
    except ReasonRequiredError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "REASON_REQUIRED", "message": str(exc)}
        ) from exc

    return RoomOut.model_validate(updated)


@router.post("/rooms/{room_id}/incidents", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
async def report_incident(
    room_id: uuid.UUID,
    body: IncidentCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("femme_de_chambre", "gouvernante")),
) -> IncidentOut:
    try:
        room = await get_room(db, room_id)
    except RoomNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, room.establishment_id)

    incident = await create_incident(
        db,
        room_id,
        room.establishment_id,
        incident_type=body.incident_type,
        description=body.description,
        photo_url=body.photo_url,
        reported_by=uuid.UUID(user.sub),
    )
    return IncidentOut.model_validate(incident)


@router.get("/rooms/{room_id}/incidents", response_model=list[IncidentOut])
async def read_incidents(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[IncidentOut]:
    try:
        room = await get_room(db, room_id)
    except RoomNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, room.establishment_id)

    incidents = await list_incidents(db, room_id)
    return [IncidentOut.model_validate(i) for i in incidents]


@router.get("/rooms/{room_id}/history", response_model=list[StatusHistoryOut])
async def read_history(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[StatusHistoryOut]:
    try:
        room = await get_room(db, room_id)
    except RoomNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, room.establishment_id)

    history = await list_status_history(db, room_id)
    return [StatusHistoryOut.model_validate(h) for h in history]


@router.post("/internal/resync/{establishment_id}", response_model=ResyncOut)
async def internal_resync(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
) -> ResyncOut:
    """Filet de sécurité D1 — appelable par un rôle service (token
    client_credentials porteur de is_super_admin=true) ou un super-admin humain."""
    count = await resync_from_establishment(db, establishment_id)
    return ResyncOut(establishment_id=establishment_id, rooms_synced=count)


@router.websocket("/ws/rooms")
async def ws_rooms(websocket: WebSocket, establishment_id: uuid.UUID, token: str) -> None:
    """Relai temps réel (§6.4, SLA <500ms) — le token JWT est passé en query
    param car l'API WebSocket du navigateur ne permet pas de header
    Authorization custom sur le handshake."""
    try:
        claims = await decode_access_token(token)
    except TokenValidationError:
        await websocket.close(code=4401)
        return

    establishment_ids = claims.get("establishment_ids", []) or []
    is_super_admin = str(claims.get("is_super_admin", "false")).lower() == "true"
    if not is_super_admin and str(establishment_id) not in establishment_ids:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    try:
        async for message in subscribe_ws_channel(str(establishment_id)):
            await websocket.send_text(message)
    except WebSocketDisconnect:
        pass
