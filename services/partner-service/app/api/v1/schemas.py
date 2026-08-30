import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PartnerCreateIn(BaseModel):
    type: str = Field(pattern="^(AGENCE|TO|CORPORATE|OTA)$")
    nom: str
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    ice: str | None = None
    rc: str | None = None
    address: str | None = None
    payment_terms: int = 30
    ota_credentials: str | None = None


class PartnerUpdateIn(BaseModel):
    nom: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    payment_terms: int | None = None
    ota_credentials: str | None = None
    is_active: bool | None = None


class PartnerOut(BaseModel):
    """`ota_credentials_encrypted` volontairement absent — jamais renvoyé,
    même chiffré, par cet endpoint."""

    id: uuid.UUID
    establishment_id: uuid.UUID
    type: str
    nom: str
    contact_name: str | None
    email: str | None
    phone: str | None
    ice: str | None
    rc: str | None
    address: str | None
    payment_terms: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
