import uuid
from datetime import datetime

from pydantic import BaseModel


class RoomOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    numero: str
    categorie: str
    floor: int
    statut: str
    motif_blocage: str | None
    blocked_reason: str | None
    blocked_at: datetime | None
    is_active: bool

    model_config = {"from_attributes": True}


class RoomStatusOut(BaseModel):
    room_id: uuid.UUID
    statut: str


class StatusChangeIn(BaseModel):
    new_status: str
    reason: str | None = None


class IncidentCreateIn(BaseModel):
    incident_type: str
    description: str | None = None
    photo_url: str | None = None


class IncidentOut(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    incident_type: str
    description: str | None
    photo_url: str | None
    reported_by: uuid.UUID
    reported_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class StatusHistoryOut(BaseModel):
    id: uuid.UUID
    old_status: str | None
    new_status: str
    changed_by: uuid.UUID
    changed_at: datetime
    reason: str | None

    model_config = {"from_attributes": True}


class ResyncOut(BaseModel):
    establishment_id: uuid.UUID
    rooms_synced: int
