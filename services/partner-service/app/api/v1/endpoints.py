import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    CurrentUser,
    assert_path_establishment_access,
    get_current_user,
    get_db,
    require_roles,
)
from app.domain.exceptions import PartnerNotFoundError
from app.domain.services import create_partner, get_partner, list_partners, soft_delete_partner, update_partner

from .schemas import PartnerCreateIn, PartnerOut, PartnerUpdateIn

router = APIRouter(prefix="/api/v1/partners", tags=["partners"])


@router.post("/{establishment_id}", response_model=PartnerOut, status_code=status.HTTP_201_CREATED)
async def create(
    establishment_id: uuid.UUID,
    body: PartnerCreateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin", "manager")),
) -> PartnerOut:
    assert_path_establishment_access(user, establishment_id)
    partner = await create_partner(db, establishment_id, **body.model_dump())
    return PartnerOut.model_validate(partner)


@router.get("/{establishment_id}", response_model=list[PartnerOut])
async def list_all(
    establishment_id: uuid.UUID,
    type: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[PartnerOut]:
    """Lecture ouverte à tout utilisateur authentifié : la réception a besoin
    de résoudre un `partner_id` pour les réservations B2B (Workflow B)."""
    assert_path_establishment_access(user, establishment_id)
    partners = await list_partners(db, establishment_id, type=type)
    return [PartnerOut.model_validate(p) for p in partners]


@router.get("/{establishment_id}/{partner_id}", response_model=PartnerOut)
async def get_one(
    establishment_id: uuid.UUID,
    partner_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> PartnerOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        partner = await get_partner(db, partner_id)
    except PartnerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    if partner.establishment_id != establishment_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(partner_id))
    return PartnerOut.model_validate(partner)


@router.patch("/{establishment_id}/{partner_id}", response_model=PartnerOut)
async def patch(
    establishment_id: uuid.UUID,
    partner_id: uuid.UUID,
    body: PartnerUpdateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin", "manager")),
) -> PartnerOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        partner = await update_partner(db, partner_id, **body.model_dump())
    except PartnerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return PartnerOut.model_validate(partner)


@router.delete("/{establishment_id}/{partner_id}", response_model=PartnerOut)
async def delete(
    establishment_id: uuid.UUID,
    partner_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin", "manager")),
) -> PartnerOut:
    assert_path_establishment_access(user, establishment_id)
    try:
        partner = await soft_delete_partner(db, partner_id)
    except PartnerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return PartnerOut.model_validate(partner)
