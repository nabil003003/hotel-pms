import uuid
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    CurrentUser,
    assert_path_establishment_access,
    get_current_user,
    get_db,
    require_roles,
)
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
from app.domain.services import (
    calculate_partner_rate,
    calculate_rate,
    create_extras_catalog_item,
    create_package,
    create_partner_rate,
    create_rate_grid,
    create_season,
    create_tax_config,
    list_extras_catalog,
    list_packages,
    list_partner_rates,
    list_rate_grid,
    list_seasons,
    list_tax_config,
    update_extras_catalog_item,
    update_package,
    update_partner_rate,
    update_rate_grid,
    update_season,
    update_tax_config,
)

from .schemas import (
    ExtrasCatalogItemCreateIn,
    ExtrasCatalogItemOut,
    ExtrasCatalogItemUpdateIn,
    PackageCreateIn,
    PackageOut,
    PackageUpdateIn,
    PartnerRateCreateIn,
    PartnerRateOut,
    PartnerRateUpdateIn,
    RateCalculateOut,
    RateGridCreateIn,
    RateGridOut,
    RateGridUpdateIn,
    SeasonCreateIn,
    SeasonOut,
    SeasonUpdateIn,
    TaxConfigCreateIn,
    TaxConfigOut,
    TaxConfigUpdateIn,
)

pricing_router = APIRouter(prefix="/api/v1/pricing", tags=["pricing"])
rates_router = APIRouter(prefix="/api/v1/rates", tags=["rates"])

# ---------------------------------------------------------------- seasons ---


@pricing_router.post("/{establishment_id}/seasons", response_model=SeasonOut, status_code=status.HTTP_201_CREATED)
async def create_season_endpoint(
    establishment_id: uuid.UUID,
    body: SeasonCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> SeasonOut:
    assert_path_establishment_access(user, establishment_id)
    season = await create_season(db, establishment_id, **body.model_dump())
    return SeasonOut.model_validate(season)


@pricing_router.get("/{establishment_id}/seasons", response_model=list[SeasonOut])
async def read_seasons(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[SeasonOut]:
    assert_path_establishment_access(user, establishment_id)
    seasons = await list_seasons(db, establishment_id)
    return [SeasonOut.model_validate(s) for s in seasons]


@pricing_router.patch("/{establishment_id}/seasons/{season_id}", response_model=SeasonOut)
async def patch_season(
    establishment_id: uuid.UUID,
    season_id: uuid.UUID,
    body: SeasonUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> SeasonOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        season = await update_season(db, season_id, **body.model_dump())
    except SeasonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return SeasonOut.model_validate(season)


# -------------------------------------------------------------- rate_grid ---


@pricing_router.post(
    "/{establishment_id}/rate-grid", response_model=RateGridOut, status_code=status.HTTP_201_CREATED
)
async def create_rate_grid_endpoint(
    establishment_id: uuid.UUID,
    body: RateGridCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> RateGridOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        row = await create_rate_grid(db, establishment_id, **body.model_dump())
    except SeasonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except RateGridAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return RateGridOut.model_validate(row)


@pricing_router.get("/{establishment_id}/rate-grid", response_model=list[RateGridOut])
async def read_rate_grid(
    establishment_id: uuid.UUID,
    room_category: str | None = None,
    season_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[RateGridOut]:
    assert_path_establishment_access(user, establishment_id)
    rows = await list_rate_grid(db, establishment_id, room_category=room_category, season_id=season_id)
    return [RateGridOut.model_validate(r) for r in rows]


@pricing_router.patch("/{establishment_id}/rate-grid/{rate_grid_id}", response_model=RateGridOut)
async def patch_rate_grid(
    establishment_id: uuid.UUID,
    rate_grid_id: uuid.UUID,
    body: RateGridUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> RateGridOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        row = await update_rate_grid(db, rate_grid_id, **body.model_dump())
    except RateGridNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return RateGridOut.model_validate(row)


# ------------------------------------------------------------ taxes_config --


@pricing_router.post("/{establishment_id}/taxes", response_model=TaxConfigOut, status_code=status.HTTP_201_CREATED)
async def create_tax_config_endpoint(
    establishment_id: uuid.UUID,
    body: TaxConfigCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> TaxConfigOut:
    assert_path_establishment_access(user, establishment_id)
    row = await create_tax_config(db, establishment_id, **body.model_dump())
    return TaxConfigOut.model_validate(row)


@pricing_router.get("/{establishment_id}/taxes", response_model=list[TaxConfigOut])
async def read_taxes(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[TaxConfigOut]:
    assert_path_establishment_access(user, establishment_id)
    rows = await list_tax_config(db, establishment_id)
    return [TaxConfigOut.model_validate(r) for r in rows]


@pricing_router.patch("/{establishment_id}/taxes/{tax_config_id}", response_model=TaxConfigOut)
async def patch_tax_config(
    establishment_id: uuid.UUID,
    tax_config_id: uuid.UUID,
    body: TaxConfigUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> TaxConfigOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        row = await update_tax_config(db, tax_config_id, **body.model_dump())
    except TaxConfigNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return TaxConfigOut.model_validate(row)


# ----------------------------------------------------------- extras_catalog -


@pricing_router.post(
    "/{establishment_id}/extras", response_model=ExtrasCatalogItemOut, status_code=status.HTTP_201_CREATED
)
async def create_extras_endpoint(
    establishment_id: uuid.UUID,
    body: ExtrasCatalogItemCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> ExtrasCatalogItemOut:
    assert_path_establishment_access(user, establishment_id)
    item = await create_extras_catalog_item(db, establishment_id, **body.model_dump())
    return ExtrasCatalogItemOut.model_validate(item)


@pricing_router.get("/{establishment_id}/extras", response_model=list[ExtrasCatalogItemOut])
async def read_extras(
    establishment_id: uuid.UUID,
    categorie: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[ExtrasCatalogItemOut]:
    assert_path_establishment_access(user, establishment_id)
    items = await list_extras_catalog(db, establishment_id, categorie=categorie)
    return [ExtrasCatalogItemOut.model_validate(i) for i in items]


@pricing_router.patch("/{establishment_id}/extras/{item_id}", response_model=ExtrasCatalogItemOut)
async def patch_extras(
    establishment_id: uuid.UUID,
    item_id: uuid.UUID,
    body: ExtrasCatalogItemUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> ExtrasCatalogItemOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        item = await update_extras_catalog_item(db, item_id, **body.model_dump())
    except ExtrasCatalogItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return ExtrasCatalogItemOut.model_validate(item)


# ------------------------------------------------------------ partner_rates -


@pricing_router.post(
    "/{establishment_id}/partner-rates", response_model=PartnerRateOut, status_code=status.HTTP_201_CREATED
)
async def create_partner_rate_endpoint(
    establishment_id: uuid.UUID,
    body: PartnerRateCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> PartnerRateOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        row = await create_partner_rate(db, establishment_id, **body.model_dump())
    except SeasonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except PartnerRateAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return PartnerRateOut.model_validate(row)


@pricing_router.get("/{establishment_id}/partner-rates", response_model=list[PartnerRateOut])
async def read_partner_rates(
    establishment_id: uuid.UUID,
    partner_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[PartnerRateOut]:
    assert_path_establishment_access(user, establishment_id)
    rows = await list_partner_rates(db, establishment_id, partner_id=partner_id)
    return [PartnerRateOut.model_validate(r) for r in rows]


@pricing_router.patch("/{establishment_id}/partner-rates/{partner_rate_id}", response_model=PartnerRateOut)
async def patch_partner_rate(
    establishment_id: uuid.UUID,
    partner_rate_id: uuid.UUID,
    body: PartnerRateUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> PartnerRateOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        row = await update_partner_rate(db, partner_rate_id, **body.model_dump())
    except PartnerRateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return PartnerRateOut.model_validate(row)


# ----------------------------------------------------------------- packages -


@pricing_router.post("/{establishment_id}/packages", response_model=PackageOut, status_code=status.HTTP_201_CREATED)
async def create_package_endpoint(
    establishment_id: uuid.UUID,
    body: PackageCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> PackageOut:
    assert_path_establishment_access(user, establishment_id)
    package = await create_package(db, establishment_id, **body.model_dump())
    return PackageOut.model_validate(package)


@pricing_router.get("/{establishment_id}/packages", response_model=list[PackageOut])
async def read_packages(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[PackageOut]:
    assert_path_establishment_access(user, establishment_id)
    packages = await list_packages(db, establishment_id)
    return [PackageOut.model_validate(p) for p in packages]


@pricing_router.patch("/{establishment_id}/packages/{package_id}", response_model=PackageOut)
async def patch_package(
    establishment_id: uuid.UUID,
    package_id: uuid.UUID,
    body: PackageUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin")),
) -> PackageOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        package = await update_package(db, package_id, **body.model_dump())
    except PackageNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return PackageOut.model_validate(package)


# ------------------------------------------------------------- rate lookup --


@rates_router.get("/calculate", response_model=RateCalculateOut)
async def get_rate_calculate(
    establishment_id: uuid.UUID,
    room_category: str,
    regime: str,
    date_from: date_type,
    date_to: date_type,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> RateCalculateOut:
    """Workflow A (spec ligne 230), appelé mid-création de réservation par
    reservation-service (ou directement par le front-office)."""
    assert_path_establishment_access(user, establishment_id)
    try:
        result = await calculate_rate(
            db, establishment_id, room_category=room_category, regime=regime, date_from=date_from, date_to=date_to
        )
    except RateNotAvailableError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return RateCalculateOut.model_validate(result)


@rates_router.get("/partner", response_model=PartnerRateOut)
async def get_rate_partner(
    establishment_id: uuid.UUID,
    partner_id: uuid.UUID,
    room_category: str,
    season_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> PartnerRateOut:
    """Workflow B (spec ligne 282) — tarif négocié agence/TO/OTA."""
    assert_path_establishment_access(user, establishment_id)
    try:
        row = await calculate_partner_rate(
            db, establishment_id, partner_id=partner_id, room_category=room_category, season_id=season_id
        )
    except PartnerRateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return PartnerRateOut.model_validate(row)
