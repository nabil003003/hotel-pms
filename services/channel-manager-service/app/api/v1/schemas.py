import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChannelConnectionCreateIn(BaseModel):
    ota_name: str = Field(pattern="^(booking_com|expedia|airbnb|direct_website)$")
    is_active: bool = True
    credentials: str | None = None
    two_way_sync_enabled: bool = False


class ChannelConnectionOut(BaseModel):
    """`credentials_encrypted` volontairement absent — jamais renvoyé."""

    id: uuid.UUID
    establishment_id: uuid.UUID
    ota_name: str
    is_active: bool
    two_way_sync_enabled: bool
    last_sync_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookBookingIn(BaseModel):
    """Workflow C (spec ligne 288-321) — payload standardisé attendu de
    chaque OTA derrière `POST /api/v1/channel/webhook/{ota_name}`."""

    ota_reference: str
    property_id: str
    room_type_id: str
    guest_name: str
    guest_email: str | None = None
    guest_phone: str | None = None
    check_in: str
    check_out: str
    adults: int = 1
    children: int = 0
    total_amount: float
    currency: str = "MAD"
    status: str = Field(pattern="^(new|modified|cancelled)$")


class WebhookResponseOut(BaseModel):
    """Sprint 3 (D6) : contrat d'origine du Workflow C (spec ligne 268-272)
    — `internal_booking_id` réel, reservation-service ayant créé la
    réservation de façon synchrone."""

    internal_booking_id: str
    status: str


class PerformanceOut(BaseModel):
    period: str
    by_ota: dict[str, dict[str, int]]
