import uuid
from datetime import date as date_type

from pydantic import BaseModel


class VerifyIn(BaseModel):
    establishment_id: uuid.UUID
    business_date: date_type


class VerifyOut(BaseModel):
    token_audit: str
    total_debits: float
    total_credits: float
    discrepancy: float
    status: str


class DiscrepancyItemOut(BaseModel):
    folio_id: uuid.UUID
    booking_id: uuid.UUID
    type: str
    balance: float


class CloseIn(BaseModel):
    establishment_id: uuid.UUID
    business_date: date_type


class CloseOut(BaseModel):
    business_date: str
    new_business_date: str
    report_hash: str
    report_urls: dict[str, str]


class BusinessDateOut(BaseModel):
    establishment_id: uuid.UUID
    business_date: str
