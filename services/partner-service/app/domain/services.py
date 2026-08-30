from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import PartnerNotFoundError
from app.domain.models import Partner
from app.infrastructure.crypto import encrypt


async def create_partner(
    db: AsyncSession, establishment_id: uuid.UUID, *, type: str, nom: str, contact_name: str | None,
    email: str | None, phone: str | None, ice: str | None, rc: str | None, address: str | None,
    payment_terms: int, ota_credentials: str | None,
) -> Partner:
    partner = Partner(
        id=uuid.uuid4(), establishment_id=establishment_id, type=type, nom=nom, contact_name=contact_name,
        email=email, phone=phone, ice=ice, rc=rc, address=address, payment_terms=payment_terms,
        ota_credentials_encrypted=encrypt(ota_credentials) if ota_credentials else None,
    )
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return partner


async def get_partner(db: AsyncSession, partner_id: uuid.UUID) -> Partner:
    partner = await db.get(Partner, partner_id)
    if partner is None:
        raise PartnerNotFoundError(str(partner_id))
    return partner


async def list_partners(
    db: AsyncSession, establishment_id: uuid.UUID, *, type: str | None = None
) -> list[Partner]:
    stmt = select(Partner).where(Partner.establishment_id == establishment_id, Partner.is_active.is_(True))
    if type is not None:
        stmt = stmt.where(Partner.type == type)
    result = await db.scalars(stmt)
    return list(result.all())


async def update_partner(db: AsyncSession, partner_id: uuid.UUID, **fields) -> Partner:
    partner = await get_partner(db, partner_id)
    ota_credentials = fields.pop("ota_credentials", None)
    if ota_credentials is not None:
        fields["ota_credentials_encrypted"] = encrypt(ota_credentials)
    for key, value in fields.items():
        if value is not None:
            setattr(partner, key, value)
    await db.commit()
    await db.refresh(partner)
    return partner


async def soft_delete_partner(db: AsyncSession, partner_id: uuid.UUID) -> Partner:
    return await update_partner(db, partner_id, is_active=False)
