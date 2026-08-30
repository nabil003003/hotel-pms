import uuid

from pydantic import BaseModel, Field


class EstablishmentCreateIn(BaseModel):
    name: str
    address: str | None = None
    city: str = "Marrakech"
    country: str = "Maroc"
    phone: str | None = None
    email: str | None = None
    total_rooms: int = Field(gt=0)


class EstablishmentUpdateIn(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool | None = None


class EstablishmentOut(BaseModel):
    id: uuid.UUID
    name: str
    address: str | None
    city: str
    country: str
    phone: str | None
    email: str | None
    total_rooms: int
    is_active: bool

    model_config = {"from_attributes": True}


class RoomCreateIn(BaseModel):
    numero: str
    categorie: str
    floor: int
    capacity_adults: int = 2
    capacity_children: int = 0


class RoomUpdateIn(BaseModel):
    numero: str | None = None
    categorie: str | None = None
    floor: int | None = None
    capacity_adults: int | None = None
    capacity_children: int | None = None


class RoomOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    numero: str
    categorie: str
    floor: int
    capacity_adults: int
    capacity_children: int
    is_active: bool

    model_config = {"from_attributes": True}


class EstablishmentServiceCreateIn(BaseModel):
    code: str
    label: str
    description: str | None = None
    prix_ht: float
    tva_rate: float = 20.00
    category: str


class EstablishmentServiceOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    code: str
    label: str
    description: str | None
    prix_ht: float
    tva_rate: float
    prix_ttc: float
    category: str
    is_active: bool

    model_config = {"from_attributes": True}


class OtaMappingUpsertIn(BaseModel):
    ota_name: str
    ota_property_id: str
    ota_room_type_id: str | None = None
    internal_room_category: str | None = None
    credentials_encrypted: str | None = None


class OtaMappingOut(BaseModel):
    """`credentials_encrypted` volontairement absent — jamais renvoyé même
    chiffré (channel-manager-service n'a besoin que du mapping room/property,
    pas des credentials OTA de establishment-service)."""

    id: uuid.UUID
    establishment_id: uuid.UUID
    ota_name: str
    ota_property_id: str
    ota_room_type_id: str | None
    internal_room_category: str | None
    is_active: bool

    model_config = {"from_attributes": True}
