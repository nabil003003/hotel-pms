import uuid
from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

# ---------------------------------------------------------- market segments -


class MarketSegmentCreateIn(BaseModel):
    code: str
    label: str
    category: str = Field(pattern="^(DIRECT|OTA|PARTENAIRES)$")
    color: str = Field(pattern="^#[0-9A-Fa-f]{6}$")


class MarketSegmentUpdateIn(BaseModel):
    label: str | None = None
    color: str | None = None
    is_active: bool | None = None


class MarketSegmentOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    code: str
    label: str
    category: str
    color: str
    is_active: bool

    model_config = {"from_attributes": True}


# ----------------------------------------------------------------- customers -


class CustomerCreateIn(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr | None = None
    phone: str | None = None
    id_number: str | None = None
    nationality: str | None = None
    date_of_birth: date_type | None = None
    is_vip: bool = False
    preferences: dict = Field(default_factory=dict)
    consent_marketing: bool = False


class CustomerUpdateIn(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    is_vip: bool | None = None
    preferences: dict | None = None
    consent_marketing: bool | None = None


class CustomerInlineIn(BaseModel):
    """Sous-schéma pour la création inline dans `POST /bookings` — chemin
    OTA (Workflow C, auto-création si client inconnu, D6)."""

    first_name: str
    last_name: str
    email: EmailStr | None = None
    phone: str | None = None


class CustomerOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    is_vip: bool
    preferences: dict
    consent_marketing: bool

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ bookings -


class BookingCreateIn(BaseModel):
    establishment_id: uuid.UUID
    market_segment_id: uuid.UUID | None = None
    market_segment_category: str | None = Field(default=None, pattern="^(DIRECT|OTA|PARTENAIRES)$")
    room_category: str
    room_id: uuid.UUID | None = None
    check_in_date: date_type
    check_out_date: date_type
    regime: str = Field(pattern="^(BB|DP|PC)$")
    taxes_payment_mode: str = Field(pattern="^(at_booking|on_site)$")
    adults: int = Field(ge=1)
    children: int = 0
    notes: str | None = None
    customer_id: uuid.UUID | None = None
    customer: CustomerInlineIn | None = None
    partner_id: uuid.UUID | None = None
    source: str = Field(
        default="walk_in",
        pattern="^(walk_in|phone|email|website|ota_booking|ota_expedia|ota_airbnb|b2b_agency)$",
    )
    ota_reference: str | None = None
    deposit_paid: bool = False

    @model_validator(mode="after")
    def _check_customer_and_dates(self) -> "BookingCreateIn":
        if self.customer_id is None and self.customer is None:
            raise ValueError("Either customer_id or customer must be provided")
        if self.market_segment_id is None and self.market_segment_category is None:
            raise ValueError("Either market_segment_id or market_segment_category must be provided")
        if self.check_out_date <= self.check_in_date:
            raise ValueError("check_out_date must be after check_in_date")
        return self


class BookingOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    customer_id: uuid.UUID
    room_id: uuid.UUID
    market_segment_id: uuid.UUID
    status: str
    option_expiry_date: datetime | None
    check_in_date: date_type
    check_out_date: date_type
    regime: str
    partner_id: uuid.UUID | None
    taxes_payment_mode: str
    total_amount: float | None
    deposit_amount: float
    adults: int
    children: int
    notes: str | None
    source: str
    ota_reference: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AvailabilityCheckIn(BaseModel):
    establishment_id: uuid.UUID
    room_id: uuid.UUID
    check_in_date: date_type
    check_out_date: date_type


class AvailabilityCheckOut(BaseModel):
    available: bool
    conflicting_booking_id: uuid.UUID | None = None


class BookingStatusUpdateIn(BaseModel):
    new_status: str = Field(
        pattern="^(status_option|status_confirmed|status_voucher|status_checked_in|"
        "status_checked_out|status_no_show|status_cancelled)$"
    )
    reason: str | None = None


class BookingRoomShiftIn(BaseModel):
    new_room_id: uuid.UUID
    new_room_category: str | None = None
    new_check_in_date: date_type | None = None
    new_check_out_date: date_type | None = None
    same_category: bool
    keep_current_rate: bool = False
    force: bool = False
    reason: str | None = None
    elevation_token: str | None = None

    @model_validator(mode="after")
    def _check_force_reason(self) -> "BookingRoomShiftIn":
        if self.force and (not self.reason or len(self.reason) < 10):
            raise ValueError("reason (min 10 chars) is required when force=true")
        return self


class BookingRoomShiftOut(BaseModel):
    booking_id: uuid.UUID
    old_room_id: uuid.UUID
    new_room_id: uuid.UUID
    new_amount: float | None
    delta: float
