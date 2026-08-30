import uuid
from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class CheckInIn(BaseModel):
    establishment_id: uuid.UUID
    booking_id: uuid.UUID


class CheckInOut(BaseModel):
    booking_id: uuid.UUID
    folio_ids: list[uuid.UUID]


class CheckOutIn(BaseModel):
    establishment_id: uuid.UUID
    booking_id: uuid.UUID


class CheckOutOut(BaseModel):
    booking_id: uuid.UUID
    folio_ids: list[uuid.UUID]


class FolioOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    booking_id: uuid.UUID
    type: str
    status: str
    third_party_ref: uuid.UUID | None
    total_charges: float
    total_payments: float
    balance: float
    opened_at: datetime
    closed_at: datetime | None
    business_date: date_type
    version: int

    model_config = {"from_attributes": True}


class ChargeCreateIn(BaseModel):
    poste_comptable: str = Field(
        pattern="^(HEB|PDJ|RES|BAR|SPA|ACT|TS|TPT|REM|HAM|TRF|DIN|EXC)$"
    )
    libelle: str
    quantity: int = Field(default=1, gt=0)
    unit_price_ht: float | None = None
    catalog_item_id: uuid.UUID | None = None
    source_service: str | None = None

    @model_validator(mode="after")
    def _check_price_source(self) -> "ChargeCreateIn":
        if self.unit_price_ht is None and self.catalog_item_id is None:
            raise ValueError("Either unit_price_ht or catalog_item_id must be provided")
        return self


class ChargeOut(BaseModel):
    id: uuid.UUID
    folio_id: uuid.UUID
    poste_comptable: str
    libelle: str
    quantity: int
    unit_price_ht: float
    montant_ht: float
    tva_rate: float
    tva_amount: float
    montant_ttc: float
    source_service: str | None
    catalog_item_id: uuid.UUID | None
    created_at: datetime
    business_date: date_type

    model_config = {"from_attributes": True}


class PaymentCreateIn(BaseModel):
    mode: str = Field(pattern="^(CB|ESP|CHQ|Virement|Débiteur)$")
    montant: float = Field(gt=0)
    reference: str | None = None


class PaymentOut(BaseModel):
    id: uuid.UUID
    folio_id: uuid.UUID
    mode: str
    montant: float
    reference: str | None
    encaisse_par: uuid.UUID
    encaisse_at: datetime
    business_date: date_type

    model_config = {"from_attributes": True}


class DailyDebitsOut(BaseModel):
    business_date: str
    total_debits: float


class DailyCreditsOut(BaseModel):
    business_date: str
    total_credits: float


class DiscrepancyItemOut(BaseModel):
    folio_id: uuid.UUID
    booking_id: uuid.UUID
    type: str
    balance: float


class CaDetailLineOut(BaseModel):
    poste_comptable: str
    montant_ht: float
    tva_amount: float
    montant_ttc: float


class DailyCaDetailOut(BaseModel):
    business_date: str
    lines: list[CaDetailLineOut]


class EncashmentLineOut(BaseModel):
    mode: str
    total: float


class DailyEncashmentsOut(BaseModel):
    business_date: str
    lines: list[EncashmentLineOut]


class DebtorItemOut(BaseModel):
    folio_id: uuid.UUID
    booking_id: uuid.UUID
    balance: float


class DeparturesOut(BaseModel):
    business_date: str
    departures: list[DebtorItemOut]
