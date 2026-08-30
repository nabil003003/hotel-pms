from __future__ import annotations

import csv
import io
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import (
    EstablishmentNotFoundError,
    InvalidCategoryError,
    InvalidCsvError,
    RoomAlreadyExistsError,
    RoomNotFoundError,
)
from app.domain.models import CANONICAL_SERVICE_CATEGORIES, Establishment, EstablishmentService, OtaMapping, Room
from app.events.publisher import (
    publish_establishment_created,
    publish_room_updated,
    publish_rooms_imported,
)


def _room_to_dict(room: Room) -> dict:
    return {
        "id": str(room.id),
        "numero": room.numero,
        "categorie": room.categorie,
        "floor": room.floor,
        "capacity_adults": room.capacity_adults,
        "capacity_children": room.capacity_children,
        "is_active": room.is_active,
    }


async def create_establishment(
    db: AsyncSession, *, name: str, address: str | None, city: str, country: str,
    phone: str | None, email: str | None, total_rooms: int,
) -> Establishment:
    establishment = Establishment(
        id=uuid.uuid4(), name=name, address=address, city=city, country=country,
        phone=phone, email=email, total_rooms=total_rooms,
    )
    db.add(establishment)
    await db.commit()
    await db.refresh(establishment)

    await publish_establishment_created(establishment.id, establishment.name)
    return establishment


async def get_establishment(db: AsyncSession, establishment_id: uuid.UUID) -> Establishment:
    establishment = await db.get(Establishment, establishment_id)
    if establishment is None:
        raise EstablishmentNotFoundError(str(establishment_id))
    return establishment


async def list_establishments(
    db: AsyncSession, *, establishment_ids: list[str] | None
) -> list[Establishment]:
    stmt = select(Establishment).where(Establishment.is_active.is_(True))
    if establishment_ids is not None:
        uuids = [uuid.UUID(eid) for eid in establishment_ids]
        stmt = stmt.where(Establishment.id.in_(uuids))
    result = await db.scalars(stmt)
    return list(result.all())


async def update_establishment(db: AsyncSession, establishment_id: uuid.UUID, **fields) -> Establishment:
    establishment = await get_establishment(db, establishment_id)
    for key, value in fields.items():
        if value is not None:
            setattr(establishment, key, value)
    await db.commit()
    await db.refresh(establishment)
    return establishment


async def create_rooms_bulk(
    db: AsyncSession, establishment_id: uuid.UUID, rooms_in: list[dict]
) -> list[Room]:
    await get_establishment(db, establishment_id)  # 404 si absent

    created: list[Room] = []
    for room_in in rooms_in:
        room = Room(id=uuid.uuid4(), establishment_id=establishment_id, **room_in)
        db.add(room)
        created.append(room)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise RoomAlreadyExistsError(str(exc)) from exc

    for room in created:
        await db.refresh(room)

    await publish_rooms_imported(establishment_id, [_room_to_dict(r) for r in created])
    return created


def parse_rooms_csv(content: bytes) -> list[dict]:
    """Colonnes attendues : numero,categorie,floor,capacity_adults,capacity_children
    (Workflow K §4.11 étape 2 — import bulk CSV)."""
    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for row in reader:
            rows.append(
                {
                    "numero": row["numero"].strip(),
                    "categorie": row["categorie"].strip(),
                    "floor": int(row["floor"]),
                    "capacity_adults": int(row.get("capacity_adults") or 2),
                    "capacity_children": int(row.get("capacity_children") or 0),
                }
            )
        if not rows:
            raise InvalidCsvError("CSV file is empty")
        return rows
    except (KeyError, ValueError) as exc:
        raise InvalidCsvError(f"Malformed CSV: {exc}") from exc


async def list_rooms(
    db: AsyncSession, establishment_id: uuid.UUID, *, categorie: str | None = None, floor: int | None = None
) -> list[Room]:
    stmt = select(Room).where(Room.establishment_id == establishment_id, Room.is_active.is_(True))
    if categorie is not None:
        stmt = stmt.where(Room.categorie == categorie)
    if floor is not None:
        stmt = stmt.where(Room.floor == floor)
    result = await db.scalars(stmt)
    return list(result.all())


async def update_room(db: AsyncSession, establishment_id: uuid.UUID, room_id: uuid.UUID, **fields) -> Room:
    room = await db.get(Room, room_id)
    if room is None or room.establishment_id != establishment_id:
        raise RoomNotFoundError(str(room_id))

    for key, value in fields.items():
        if value is not None:
            setattr(room, key, value)
    await db.commit()
    await db.refresh(room)

    await publish_room_updated(establishment_id, _room_to_dict(room))
    return room


async def soft_delete_room(db: AsyncSession, establishment_id: uuid.UUID, room_id: uuid.UUID) -> Room:
    return await update_room(db, establishment_id, room_id, is_active=False)


async def create_establishment_service(
    db: AsyncSession, establishment_id: uuid.UUID, *, code: str, label: str, description: str | None,
    prix_ht: float, tva_rate: float, category: str,
) -> EstablishmentService:
    await get_establishment(db, establishment_id)
    if category not in CANONICAL_SERVICE_CATEGORIES:
        raise InvalidCategoryError(
            f"category must be one of {CANONICAL_SERVICE_CATEGORIES}, got {category!r}"
        )
    prix_ttc = round(float(prix_ht) * (1 + float(tva_rate) / 100), 2)
    service = EstablishmentService(
        id=uuid.uuid4(), establishment_id=establishment_id, code=code, label=label,
        description=description, prix_ht=prix_ht, tva_rate=tva_rate, prix_ttc=prix_ttc, category=category,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


async def list_establishment_services(db: AsyncSession, establishment_id: uuid.UUID) -> list[EstablishmentService]:
    stmt = select(EstablishmentService).where(
        EstablishmentService.establishment_id == establishment_id,
        EstablishmentService.is_active.is_(True),
    )
    result = await db.scalars(stmt)
    return list(result.all())


async def upsert_ota_mapping(
    db: AsyncSession, establishment_id: uuid.UUID, *, ota_name: str, ota_property_id: str,
    ota_room_type_id: str | None, internal_room_category: str | None, credentials_encrypted: str | None,
) -> OtaMapping:
    """Sprint 2 (D3, option 1) : establishment-service reste seul propriétaire
    de `ota_mappings` ; channel-manager-service la lit en REST plutôt que de
    la dupliquer dans `channel_db`."""
    await get_establishment(db, establishment_id)  # 404 si absent

    stmt = select(OtaMapping).where(
        OtaMapping.establishment_id == establishment_id,
        OtaMapping.ota_name == ota_name,
        OtaMapping.ota_room_type_id == ota_room_type_id,
    )
    existing = (await db.scalars(stmt)).first()
    if existing is not None:
        existing.ota_property_id = ota_property_id
        existing.internal_room_category = internal_room_category
        if credentials_encrypted is not None:
            existing.credentials_encrypted = credentials_encrypted
        mapping = existing
    else:
        mapping = OtaMapping(
            id=uuid.uuid4(), establishment_id=establishment_id, ota_name=ota_name,
            ota_property_id=ota_property_id, ota_room_type_id=ota_room_type_id,
            internal_room_category=internal_room_category, credentials_encrypted=credentials_encrypted,
        )
        db.add(mapping)

    await db.commit()
    await db.refresh(mapping)
    return mapping


async def list_ota_mappings(
    db: AsyncSession, establishment_id: uuid.UUID, *, ota_name: str | None = None,
    ota_room_type_id: str | None = None,
) -> list[OtaMapping]:
    stmt = select(OtaMapping).where(
        OtaMapping.establishment_id == establishment_id, OtaMapping.is_active.is_(True)
    )
    if ota_name is not None:
        stmt = stmt.where(OtaMapping.ota_name == ota_name)
    if ota_room_type_id is not None:
        stmt = stmt.where(OtaMapping.ota_room_type_id == ota_room_type_id)
    result = await db.scalars(stmt)
    return list(result.all())
