import uuid
from datetime import date as date_type

from fastapi import APIRouter, Depends, Header, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    CurrentUser,
    assert_path_establishment_access,
    get_current_user,
    get_db,
    require_roles,
)
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
from app.domain.services import (
    check_availability,
    create_booking,
    create_customer,
    create_market_segment,
    get_booking,
    get_customer,
    get_market_segment,
    list_bookings,
    list_customers,
    list_market_segments,
    shift_room,
    update_booking_status,
    update_customer,
    update_market_segment,
)
from app.infrastructure import redis_client as locks
from app.infrastructure.keycloak import TokenValidationError, decode_access_token

from .schemas import (
    AvailabilityCheckIn,
    AvailabilityCheckOut,
    BookingCreateIn,
    BookingOut,
    BookingRoomShiftIn,
    BookingRoomShiftOut,
    BookingStatusUpdateIn,
    CustomerCreateIn,
    CustomerOut,
    CustomerUpdateIn,
    MarketSegmentCreateIn,
    MarketSegmentOut,
    MarketSegmentUpdateIn,
)

segments_router = APIRouter(prefix="/api/v1/market-segments", tags=["market-segments"])
customers_router = APIRouter(prefix="/api/v1/customers", tags=["customers"])
bookings_router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])
planning_router = APIRouter(prefix="/api/v1/planning", tags=["planning"])
ws_router = APIRouter(prefix="/api/v1", tags=["planning-ws"])

# ---------------------------------------------------------- market segments -


@segments_router.post("/{establishment_id}", response_model=MarketSegmentOut, status_code=status.HTTP_201_CREATED)
async def create_segment(
    establishment_id: uuid.UUID,
    body: MarketSegmentCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> MarketSegmentOut:
    assert_path_establishment_access(user, establishment_id)
    segment = await create_market_segment(db, establishment_id, **body.model_dump())
    return MarketSegmentOut.model_validate(segment)


@segments_router.get("/{establishment_id}", response_model=list[MarketSegmentOut])
async def read_segments(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[MarketSegmentOut]:
    assert_path_establishment_access(user, establishment_id)
    segments = await list_market_segments(db, establishment_id)
    return [MarketSegmentOut.model_validate(s) for s in segments]


@segments_router.patch("/{establishment_id}/{segment_id}", response_model=MarketSegmentOut)
async def patch_segment(
    establishment_id: uuid.UUID,
    segment_id: uuid.UUID,
    body: MarketSegmentUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> MarketSegmentOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        segment = await update_market_segment(db, segment_id, **body.model_dump())
    except MarketSegmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return MarketSegmentOut.model_validate(segment)


# ----------------------------------------------------------------- customers -


@customers_router.post("/{establishment_id}", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
async def create_customer_endpoint(
    establishment_id: uuid.UUID,
    body: CustomerCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> CustomerOut:
    """Workflow A étape 3 (spec ligne 225) — ouvert à tout utilisateur
    authentifié, la réception crée les fiches client."""
    assert_path_establishment_access(user, establishment_id)
    customer = await create_customer(db, establishment_id, **body.model_dump())
    return CustomerOut.model_validate(customer)


@customers_router.get("/{establishment_id}", response_model=list[CustomerOut])
async def read_customers(
    establishment_id: uuid.UUID,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[CustomerOut]:
    """Autocomplete (spec ligne 224 — debounce/min-length côté frontend)."""
    assert_path_establishment_access(user, establishment_id)
    customers = await list_customers(db, establishment_id, search=search)
    return [CustomerOut.model_validate(c) for c in customers]


@customers_router.get("/{establishment_id}/{customer_id}", response_model=CustomerOut)
async def read_customer(
    establishment_id: uuid.UUID,
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> CustomerOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        customer = await get_customer(db, customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    if customer.establishment_id != establishment_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(customer_id))
    return CustomerOut.model_validate(customer)


@customers_router.patch("/{establishment_id}/{customer_id}", response_model=CustomerOut)
async def patch_customer(
    establishment_id: uuid.UUID,
    customer_id: uuid.UUID,
    body: CustomerUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> CustomerOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        customer = await update_customer(db, customer_id, **body.model_dump())
    except CustomerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return CustomerOut.model_validate(customer)


# ------------------------------------------------------------------ bookings -


@bookings_router.post("/check-availability", response_model=AvailabilityCheckOut)
async def check_availability_endpoint(
    body: AvailabilityCheckIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("receptionniste", "manager", "admin")),
) -> AvailabilityCheckOut:
    assert_path_establishment_access(user, body.establishment_id)
    conflict = await check_availability(
        db, body.establishment_id, body.room_id, body.check_in_date, body.check_out_date
    )
    return AvailabilityCheckOut(available=conflict is None, conflicting_booking_id=conflict)


@bookings_router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking_endpoint(
    body: BookingCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("receptionniste", "manager", "admin")),
    x_idempotency_key: str | None = Header(None, alias="X-Idempotency-Key"),
) -> BookingOut:
    """Workflows A/B/C (spec §4.1/4.2/4.3). Accessible aux comptes de
    service `is_super_admin` (ex: `svc-channel-manager` pour le chemin OTA
    synchrone, D6) via le bypass de `require_roles`."""
    assert_path_establishment_access(user, body.establishment_id)

    if x_idempotency_key:
        cached_id = await locks.get_idempotent_booking_id(x_idempotency_key)
        if cached_id:
            booking = await get_booking(db, uuid.UUID(cached_id))
            return BookingOut.model_validate(booking)

    fields = body.model_dump(exclude={"establishment_id", "customer"})
    try:
        booking = await create_booking(
            db, body.establishment_id, customer=body.customer.model_dump() if body.customer else None,
            created_by=uuid.UUID(user.sub), **fields,
        )
    except MarketSegmentNotFoundError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"code": "INVALID_SEGMENT", "message": str(exc)}) from exc
    except InvalidSegmentError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"code": "INVALID_SEGMENT", "message": str(exc)}) from exc
    except CustomerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except NoRoomAvailableError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"code": "NO_ROOM_AVAILABLE", "message": str(exc)}) from exc
    except RoomUnavailableError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, {"code": "ROOM_UNAVAILABLE", "message": str(exc)}) from exc
    except BusinessDateLockedError as exc:
        raise HTTPException(status.HTTP_423_LOCKED, str(exc)) from exc

    if x_idempotency_key:
        await locks.set_idempotent_booking_id(x_idempotency_key, str(booking.id))

    return BookingOut.model_validate(booking)


@bookings_router.get("", response_model=list[BookingOut])
async def read_bookings(
    establishment_id: uuid.UUID,
    from_date: date_type | None = None,
    to_date: date_type | None = None,
    check_in_date: date_type | None = None,
    check_out_date: date_type | None = None,
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[BookingOut]:
    """`check_in_date`/`check_out_date` (filtres exacts, distincts de
    `from_date`/`to_date`) et `status` : ajoutés Sprint 5 (D12) pour les
    rapports "arrivées prévues J+1"/"départs attendus J+1" de
    night-audit-service."""
    assert_path_establishment_access(user, establishment_id)
    bookings = await list_bookings(
        db, establishment_id, from_date=from_date, to_date=to_date,
        check_in_date=check_in_date, check_out_date=check_out_date, status=status_filter,
    )
    return [BookingOut.model_validate(b) for b in bookings]


@bookings_router.get("/{booking_id}", response_model=BookingOut)
async def read_booking(
    booking_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> BookingOut:
    try:
        booking = await get_booking(db, booking_id)
    except BookingNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, booking.establishment_id)
    return BookingOut.model_validate(booking)


@bookings_router.patch("/{booking_id}/status", response_model=BookingOut)
async def patch_booking_status(
    booking_id: uuid.UUID,
    body: BookingStatusUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("receptionniste", "manager", "admin")),
) -> BookingOut:
    try:
        existing = await get_booking(db, booking_id)
    except BookingNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, existing.establishment_id)
    try:
        booking = await update_booking_status(
            db, booking_id, body.new_status, changed_by=uuid.UUID(user.sub), reason=body.reason
        )
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, {"code": "INVALID_TRANSITION", "message": str(exc)}) from exc
    except BusinessDateLockedError as exc:
        raise HTTPException(status.HTTP_423_LOCKED, str(exc)) from exc
    return BookingOut.model_validate(booking)


@bookings_router.patch("/{booking_id}/room", response_model=BookingRoomShiftOut)
async def patch_booking_room(
    booking_id: uuid.UUID,
    body: BookingRoomShiftIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("receptionniste", "manager", "admin")),
) -> BookingRoomShiftOut:
    """Workflow F (spec §4.6, décision D8)."""
    try:
        existing = await get_booking(db, booking_id)
    except BookingNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, existing.establishment_id)
    try:
        result = await shift_room(
            db, booking_id, new_room_id=body.new_room_id, new_room_category=body.new_room_category,
            new_check_in_date=body.new_check_in_date, new_check_out_date=body.new_check_out_date,
            same_category=body.same_category, keep_current_rate=body.keep_current_rate, force=body.force,
            reason=body.reason, elevation_token=body.elevation_token, actor=uuid.UUID(user.sub),
        )
    except UpsellRequiresValidationError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, {"code": "UPSELL_REQUIRES_MANAGER", "message": str(exc)}
        ) from exc
    except ElevationInvalidError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    except RoomConflictError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"code": "ROOM_CONFLICT", "message": str(exc), "conflicting_booking_id": str(exc.conflicting_booking_id)},
        ) from exc
    except RoomShiftLockedError as exc:
        raise HTTPException(
            status.HTTP_423_LOCKED, {"code": "ROOM_SHIFT_IN_PROGRESS", "message": str(exc), "retry_after": 30}
        ) from exc
    return BookingRoomShiftOut.model_validate(result)


# ------------------------------------------------------------------ planning -


@planning_router.get("", response_model=list[BookingOut])
async def read_planning(
    establishment_id: uuid.UUID,
    from_date: date_type = Query(..., alias="from"),
    to_date: date_type = Query(..., alias="to"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[BookingOut]:
    """`GET /api/v1/planning?from&to&establishment_id` (Workflow A étape 1,
    spec ligne 223) — vue simplifiée Sprint 3 : liste des réservations
    chevauchant la période, pas de rendu calendrier (Sprint 6 frontend)."""
    assert_path_establishment_access(user, establishment_id)
    bookings = await list_bookings(db, establishment_id, from_date=from_date, to_date=to_date)
    return [BookingOut.model_validate(b) for b in bookings]


# --------------------------------------------------------------- planning ws -


@ws_router.websocket("/ws/planning")
async def ws_planning(websocket: WebSocket, establishment_id: uuid.UUID, token: str) -> None:
    """Relai temps réel pour la grille planning (drag & drop) — même pattern
    que housekeeping-service `/ws/rooms` : le token JWT est passé en query
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
        async for message in locks.subscribe_ws_channel(str(establishment_id)):
            await websocket.send_text(message)
    except WebSocketDisconnect:
        pass
