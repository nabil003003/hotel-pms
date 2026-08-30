import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    CurrentUser,
    assert_path_establishment_access,
    get_current_user,
    get_db,
    require_roles,
    require_super_admin,
)
from app.domain.exceptions import (
    EstablishmentNotFoundError,
    InvalidCategoryError,
    InvalidCsvError,
    RoomAlreadyExistsError,
    RoomNotFoundError,
)
from app.domain.services import (
    create_establishment,
    create_establishment_service,
    create_rooms_bulk,
    get_establishment,
    list_establishment_services,
    list_establishments,
    list_ota_mappings,
    list_rooms,
    parse_rooms_csv,
    soft_delete_room,
    update_establishment,
    update_room,
    upsert_ota_mapping,
)

from .schemas import (
    EstablishmentCreateIn,
    EstablishmentOut,
    EstablishmentServiceCreateIn,
    EstablishmentServiceOut,
    EstablishmentUpdateIn,
    OtaMappingOut,
    OtaMappingUpsertIn,
    RoomCreateIn,
    RoomOut,
    RoomUpdateIn,
)

router = APIRouter(prefix="/api/v1/establishments", tags=["establishments"])


@router.post("", response_model=EstablishmentOut, status_code=status.HTTP_201_CREATED)
async def create(
    body: EstablishmentCreateIn,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
) -> EstablishmentOut:
    establishment = await create_establishment(db, **body.model_dump())
    return EstablishmentOut.model_validate(establishment)


@router.get("", response_model=list[EstablishmentOut])
async def list_all(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> list[EstablishmentOut]:
    ids = None if user.is_super_admin else user.establishment_ids
    establishments = await list_establishments(db, establishment_ids=ids)
    return [EstablishmentOut.model_validate(e) for e in establishments]


@router.get("/{establishment_id}", response_model=EstablishmentOut)
async def get_one(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> EstablishmentOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        establishment = await get_establishment(db, establishment_id)
    except EstablishmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return EstablishmentOut.model_validate(establishment)


@router.patch("/{establishment_id}", response_model=EstablishmentOut)
async def update(
    establishment_id: uuid.UUID,
    body: EstablishmentUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> EstablishmentOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        establishment = await update_establishment(db, establishment_id, **body.model_dump())
    except EstablishmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return EstablishmentOut.model_validate(establishment)


@router.post("/{establishment_id}/rooms", response_model=list[RoomOut], status_code=status.HTTP_201_CREATED)
async def create_rooms(
    establishment_id: uuid.UUID,
    body: list[RoomCreateIn],
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> list[RoomOut]:
    assert_path_establishment_access(user, establishment_id)
    try:
        rooms = await create_rooms_bulk(db, establishment_id, [r.model_dump() for r in body])
    except EstablishmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except RoomAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return [RoomOut.model_validate(r) for r in rooms]


@router.post(
    "/{establishment_id}/rooms/bulk-csv", response_model=list[RoomOut], status_code=status.HTTP_201_CREATED
)
async def create_rooms_from_csv(
    establishment_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> list[RoomOut]:
    """Workflow K §4.11 étape 2 — import bulk de chambres via CSV."""
    assert_path_establishment_access(user, establishment_id)
    content = await file.read()
    try:
        rows = parse_rooms_csv(content)
        rooms = await create_rooms_bulk(db, establishment_id, rows)
    except InvalidCsvError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except EstablishmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except RoomAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return [RoomOut.model_validate(r) for r in rooms]


@router.get("/{establishment_id}/rooms", response_model=list[RoomOut])
async def read_rooms(
    establishment_id: uuid.UUID,
    categorie: str | None = None,
    floor: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[RoomOut]:
    assert_path_establishment_access(user, establishment_id)
    rooms = await list_rooms(db, establishment_id, categorie=categorie, floor=floor)
    return [RoomOut.model_validate(r) for r in rooms]


@router.patch("/{establishment_id}/rooms/{room_id}", response_model=RoomOut)
async def patch_room(
    establishment_id: uuid.UUID,
    room_id: uuid.UUID,
    body: RoomUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> RoomOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        room = await update_room(db, establishment_id, room_id, **body.model_dump())
    except RoomNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return RoomOut.model_validate(room)


@router.delete("/{establishment_id}/rooms/{room_id}", response_model=RoomOut)
async def delete_room(
    establishment_id: uuid.UUID,
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> RoomOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        room = await soft_delete_room(db, establishment_id, room_id)
    except RoomNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return RoomOut.model_validate(room)


@router.post(
    "/{establishment_id}/services", response_model=EstablishmentServiceOut, status_code=status.HTTP_201_CREATED
)
async def create_service(
    establishment_id: uuid.UUID,
    body: EstablishmentServiceCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> EstablishmentServiceOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        service = await create_establishment_service(db, establishment_id, **body.model_dump())
    except EstablishmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidCategoryError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return EstablishmentServiceOut.model_validate(service)


@router.get("/{establishment_id}/services", response_model=list[EstablishmentServiceOut])
async def read_services(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[EstablishmentServiceOut]:
    assert_path_establishment_access(user, establishment_id)
    services = await list_establishment_services(db, establishment_id)
    return [EstablishmentServiceOut.model_validate(s) for s in services]


@router.post("/{establishment_id}/ota-mappings", response_model=OtaMappingOut, status_code=status.HTTP_201_CREATED)
async def upsert_ota_mapping_endpoint(
    establishment_id: uuid.UUID,
    body: OtaMappingUpsertIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> OtaMappingOut:
    """D3 (Sprint 2) : `ota_mappings` reste dans establishment_db, configurée
    ici par un admin (Workflow K étape 5) puis lue en REST par
    channel-manager-service."""
    assert_path_establishment_access(user, establishment_id)
    try:
        mapping = await upsert_ota_mapping(db, establishment_id, **body.model_dump())
    except EstablishmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return OtaMappingOut.model_validate(mapping)


@router.get("/{establishment_id}/ota-mappings", response_model=list[OtaMappingOut])
async def read_ota_mappings(
    establishment_id: uuid.UUID,
    ota_name: str | None = None,
    ota_room_type_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[OtaMappingOut]:
    assert_path_establishment_access(user, establishment_id)
    mappings = await list_ota_mappings(db, establishment_id, ota_name=ota_name, ota_room_type_id=ota_room_type_id)
    return [OtaMappingOut.model_validate(m) for m in mappings]
