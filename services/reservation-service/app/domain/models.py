"""Transcription littérale du spec §5.2 (lignes 827-948) : bookings,
market_segments, customers, booking_status_history, audit_log.

Sprint 3 — schéma posé à l'avance, aucun endpoint n'existe encore."""

import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class MarketSegment(Base):
    __tablename__ = "market_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("category IN ('DIRECT','OTA','PARTENAIRES')", name="chk_market_segments_category"),
        UniqueConstraint("establishment_id", "code", name="uq_market_segments_establishment_code"),
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))
    id_number: Mapped[str | None] = mapped_column(String(50))
    nationality: Mapped[str | None] = mapped_column(String(3))
    date_of_birth: Mapped[date_type | None] = mapped_column(Date)
    historical_notes: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_vip: Mapped[bool] = mapped_column(default=False)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    consent_marketing: Mapped[bool] = mapped_column(default=False)
    anonymized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    market_segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("market_segments.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    option_expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    check_in_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    regime: Mapped[str] = mapped_column(String(5), nullable=False)
    partner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    taxes_payment_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    total_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    deposit_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    adults: Mapped[int] = mapped_column(Integer, nullable=False)
    children: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="walk_in")
    ota_reference: Mapped[str | None] = mapped_column(String(100))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "status IN ('status_option','status_confirmed','status_voucher','status_checked_in',"
            "'status_checked_out','status_no_show','status_cancelled')",
            name="chk_bookings_status",
        ),
        CheckConstraint("regime IN ('BB','DP','PC')", name="chk_bookings_regime"),
        CheckConstraint(
            "taxes_payment_mode IN ('at_booking','on_site')", name="chk_bookings_taxes_payment_mode"
        ),
        CheckConstraint("adults > 0", name="chk_bookings_adults_positive"),
        CheckConstraint("children >= 0", name="chk_bookings_children_non_negative"),
        CheckConstraint(
            "source IN ('walk_in','phone','email','website','ota_booking','ota_expedia','ota_airbnb','b2b_agency')",
            name="chk_bookings_source",
        ),
        CheckConstraint("check_out_date > check_in_date", name="chk_dates"),
        CheckConstraint(
            "status != 'status_option' OR option_expiry_date IS NOT NULL", name="chk_option_date"
        ),
    )


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reason: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(INET)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class BusinessDateLock(Base):
    """Pas dans la transcription §5.2 — ajouté Sprint 5 (D12) : le spec (ligne
    620) dit explicitement que front-office-service ET reservation-service
    activent `business_date_locked`. Même schéma que front-office-service
    (`business_date_locks`, Sprint 4)."""

    __tablename__ = "business_date_locks"

    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    business_date: Mapped[date_type] = mapped_column(Date, primary_key=True)
    is_locked: Mapped[bool] = mapped_column(default=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    old_data: Mapped[dict | None] = mapped_column(JSONB)
    new_data: Mapped[dict | None] = mapped_column(JSONB)
    performed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ip_address: Mapped[str | None] = mapped_column(INET)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    __table_args__ = (CheckConstraint("action IN ('INSERT','UPDATE','DELETE')", name="chk_audit_log_action"),)
