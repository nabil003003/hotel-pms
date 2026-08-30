from __future__ import annotations

import uuid
from datetime import date as date_type
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import (
    ExtrasCatalogItemNotFoundError,
    PackageNotFoundError,
    PartnerRateAlreadyExistsError,
    PartnerRateNotFoundError,
    RateGridAlreadyExistsError,
    RateGridNotFoundError,
    RateNotAvailableError,
    SeasonNotFoundError,
    TaxConfigNotFoundError,
)
from app.domain.models import ExtrasCatalogItem, Package, PartnerRate, RateGrid, Season, TaxConfig

# ---------------------------------------------------------------- seasons ---


async def create_season(db: AsyncSession, establishment_id: uuid.UUID, **fields) -> Season:
    season = Season(id=uuid.uuid4(), establishment_id=establishment_id, **fields)
    db.add(season)
    await db.commit()
    await db.refresh(season)
    return season


async def get_season(db: AsyncSession, season_id: uuid.UUID) -> Season:
    season = await db.get(Season, season_id)
    if season is None:
        raise SeasonNotFoundError(str(season_id))
    return season


async def list_seasons(db: AsyncSession, establishment_id: uuid.UUID) -> list[Season]:
    stmt = select(Season).where(Season.establishment_id == establishment_id, Season.is_active.is_(True))
    result = await db.scalars(stmt)
    return list(result.all())


async def update_season(db: AsyncSession, season_id: uuid.UUID, **fields) -> Season:
    season = await get_season(db, season_id)
    for key, value in fields.items():
        if value is not None:
            setattr(season, key, value)
    await db.commit()
    await db.refresh(season)
    return season


# -------------------------------------------------------------- rate_grid ---


async def create_rate_grid(db: AsyncSession, establishment_id: uuid.UUID, **fields) -> RateGrid:
    await get_season(db, fields["season_id"])  # 404 si absent
    row = RateGrid(id=uuid.uuid4(), establishment_id=establishment_id, **fields)
    db.add(row)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise RateGridAlreadyExistsError(str(exc)) from exc
    await db.refresh(row)
    return row


async def get_rate_grid(db: AsyncSession, rate_grid_id: uuid.UUID) -> RateGrid:
    row = await db.get(RateGrid, rate_grid_id)
    if row is None:
        raise RateGridNotFoundError(str(rate_grid_id))
    return row


async def list_rate_grid(
    db: AsyncSession, establishment_id: uuid.UUID, *, room_category: str | None = None,
    season_id: uuid.UUID | None = None,
) -> list[RateGrid]:
    stmt = select(RateGrid).where(RateGrid.establishment_id == establishment_id)
    if room_category is not None:
        stmt = stmt.where(RateGrid.room_category == room_category)
    if season_id is not None:
        stmt = stmt.where(RateGrid.season_id == season_id)
    result = await db.scalars(stmt)
    return list(result.all())


async def update_rate_grid(db: AsyncSession, rate_grid_id: uuid.UUID, **fields) -> RateGrid:
    row = await get_rate_grid(db, rate_grid_id)
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return row


# ------------------------------------------------------------ taxes_config --


async def create_tax_config(db: AsyncSession, establishment_id: uuid.UUID, **fields) -> TaxConfig:
    row = TaxConfig(id=uuid.uuid4(), establishment_id=establishment_id, **fields)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_tax_config(db: AsyncSession, tax_config_id: uuid.UUID) -> TaxConfig:
    row = await db.get(TaxConfig, tax_config_id)
    if row is None:
        raise TaxConfigNotFoundError(str(tax_config_id))
    return row


async def list_tax_config(db: AsyncSession, establishment_id: uuid.UUID) -> list[TaxConfig]:
    stmt = select(TaxConfig).where(TaxConfig.establishment_id == establishment_id, TaxConfig.is_active.is_(True))
    result = await db.scalars(stmt)
    return list(result.all())


async def update_tax_config(db: AsyncSession, tax_config_id: uuid.UUID, **fields) -> TaxConfig:
    row = await get_tax_config(db, tax_config_id)
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return row


# ----------------------------------------------------------- extras_catalog -


async def create_extras_catalog_item(
    db: AsyncSession, establishment_id: uuid.UUID, *, categorie: str, libelle: str, description: str | None,
    prix_ht: float, tva_rate: float,
) -> ExtrasCatalogItem:
    prix_ttc = round(float(prix_ht) * (1 + float(tva_rate) / 100), 2)
    item = ExtrasCatalogItem(
        id=uuid.uuid4(), establishment_id=establishment_id, categorie=categorie, libelle=libelle,
        description=description, prix_ht=prix_ht, tva_rate=tva_rate, prix_ttc=prix_ttc,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_extras_catalog_item(db: AsyncSession, item_id: uuid.UUID) -> ExtrasCatalogItem:
    item = await db.get(ExtrasCatalogItem, item_id)
    if item is None:
        raise ExtrasCatalogItemNotFoundError(str(item_id))
    return item


async def list_extras_catalog(
    db: AsyncSession, establishment_id: uuid.UUID, *, categorie: str | None = None
) -> list[ExtrasCatalogItem]:
    stmt = select(ExtrasCatalogItem).where(
        ExtrasCatalogItem.establishment_id == establishment_id, ExtrasCatalogItem.is_active.is_(True)
    )
    if categorie is not None:
        stmt = stmt.where(ExtrasCatalogItem.categorie == categorie)
    result = await db.scalars(stmt)
    return list(result.all())


async def update_extras_catalog_item(db: AsyncSession, item_id: uuid.UUID, **fields) -> ExtrasCatalogItem:
    item = await get_extras_catalog_item(db, item_id)
    for key, value in fields.items():
        if value is not None:
            setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


# ------------------------------------------------------------ partner_rates -


async def create_partner_rate(db: AsyncSession, establishment_id: uuid.UUID, **fields) -> PartnerRate:
    await get_season(db, fields["season_id"])  # 404 si absent
    row = PartnerRate(id=uuid.uuid4(), establishment_id=establishment_id, **fields)
    db.add(row)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise PartnerRateAlreadyExistsError(str(exc)) from exc
    await db.refresh(row)
    return row


async def get_partner_rate(db: AsyncSession, partner_rate_id: uuid.UUID) -> PartnerRate:
    row = await db.get(PartnerRate, partner_rate_id)
    if row is None:
        raise PartnerRateNotFoundError(str(partner_rate_id))
    return row


async def list_partner_rates(
    db: AsyncSession, establishment_id: uuid.UUID, *, partner_id: uuid.UUID | None = None
) -> list[PartnerRate]:
    stmt = select(PartnerRate).where(PartnerRate.establishment_id == establishment_id)
    if partner_id is not None:
        stmt = stmt.where(PartnerRate.partner_id == partner_id)
    result = await db.scalars(stmt)
    return list(result.all())


async def update_partner_rate(db: AsyncSession, partner_rate_id: uuid.UUID, **fields) -> PartnerRate:
    row = await get_partner_rate(db, partner_rate_id)
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return row


# ----------------------------------------------------------------- packages -


async def create_package(db: AsyncSession, establishment_id: uuid.UUID, **fields) -> Package:
    package = Package(id=uuid.uuid4(), establishment_id=establishment_id, **fields)
    db.add(package)
    await db.commit()
    await db.refresh(package)
    return package


async def get_package(db: AsyncSession, package_id: uuid.UUID) -> Package:
    package = await db.get(Package, package_id)
    if package is None:
        raise PackageNotFoundError(str(package_id))
    return package


async def list_packages(db: AsyncSession, establishment_id: uuid.UUID) -> list[Package]:
    stmt = select(Package).where(Package.establishment_id == establishment_id, Package.is_active.is_(True))
    result = await db.scalars(stmt)
    return list(result.all())


async def update_package(db: AsyncSession, package_id: uuid.UUID, **fields) -> Package:
    package = await get_package(db, package_id)
    for key, value in fields.items():
        if value is not None:
            setattr(package, key, value)
    await db.commit()
    await db.refresh(package)
    return package


# ------------------------------------------------------------- rate lookup --


def _resolve_season_for_night(seasons: list[Season], night: date_type) -> Season | None:
    for season in seasons:
        if season.date_debut <= night < season.date_fin:
            return season
    return None


async def calculate_rate(
    db: AsyncSession, establishment_id: uuid.UUID, *, room_category: str, regime: str,
    date_from: date_type, date_to: date_type,
) -> dict:
    """Workflow A (spec ligne 230) : `GET /api/v1/rates/calculate` — résout la
    season applicable nuit par nuit (une réservation peut chevaucher deux
    saisons) puis somme `rate_grid.prix_ttc`. Lève RateNotAvailableError dès
    qu'une nuit n'a ni season ni rate_grid correspondant — laisser
    reservation-service décider de dégrader en `status_option` sans tarif
    (règle de résilience, spec ligne 1353) plutôt que de deviner un prix ici."""
    if date_to <= date_from:
        raise RateNotAvailableError("date_to must be after date_from")

    seasons = await list_seasons(db, establishment_id)
    rate_grid_rows = await list_rate_grid(db, establishment_id, room_category=room_category)
    rates_by_season = {row.season_id: row for row in rate_grid_rows if row.regime == regime}

    nights: list[dict] = []
    total_ttc = 0.0
    night = date_from
    while night < date_to:
        season = _resolve_season_for_night(seasons, night)
        rate = rates_by_season.get(season.id) if season is not None else None
        if season is None or rate is None:
            raise RateNotAvailableError(f"No rate for {room_category}/{regime} on {night.isoformat()}")
        nights.append({"date": night.isoformat(), "season_id": str(season.id), "prix_ttc": float(rate.prix_ttc)})
        total_ttc += float(rate.prix_ttc)
        night += timedelta(days=1)

    return {"room_category": room_category, "regime": regime, "nights": nights, "total_ttc": round(total_ttc, 2)}


async def calculate_partner_rate(
    db: AsyncSession, establishment_id: uuid.UUID, *, partner_id: uuid.UUID, room_category: str,
    season_id: uuid.UUID,
) -> PartnerRate:
    """Workflow B (spec ligne 282) : `GET /api/v1/rates/partner` — tarif
    négocié, ne fait pas de sommation par nuit (contrairement à
    calculate_rate) car il s'applique tel quel pour toute la saison donnée."""
    stmt = select(PartnerRate).where(
        PartnerRate.establishment_id == establishment_id,
        PartnerRate.partner_id == partner_id,
        PartnerRate.room_category == room_category,
        PartnerRate.season_id == season_id,
    )
    row = (await db.scalars(stmt)).first()
    if row is None:
        raise PartnerRateNotFoundError(
            f"No negotiated rate for partner={partner_id} category={room_category} season={season_id}"
        )
    return row
