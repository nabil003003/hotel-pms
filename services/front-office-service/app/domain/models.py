"""Transcription littérale du spec §5.3 (lignes 950-1029) : folios,
folio_charges, payments, business_date_locks.

Sprint 4 — schéma posé à l'avance, aucun endpoint n'existe encore.

`Folio.version` est un ajout (pas dans la transcription §5.3) : §6.2
(ligne 1335) exige un verrouillage optimiste "via colonne `version`" sur
les folios, absente du DDL littéral. Incrément manuel vérifié dans
`domain/services.py` (charges/paiements), pas le mécanisme
`version_id_col` de SQLAlchemy (incompatible avec le flux
commit/refresh explicite déjà utilisé partout ailleurs dans ce
monorepo)."""

import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class Folio(Base):
    __tablename__ = "folios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    type: Mapped[str] = mapped_column(String(1), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="open")
    third_party_ref: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    total_charges: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_payments: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    balance: Mapped[float] = mapped_column(
        Numeric(12, 2), Computed("total_charges - total_payments", persisted=True)
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    business_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    __table_args__ = (
        CheckConstraint("type IN ('A','B')", name="chk_folios_type"),
        CheckConstraint("status IN ('open','closed')", name="chk_folios_status"),
    )


class FolioCharge(Base):
    __tablename__ = "folio_charges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    folio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("folios.id"), nullable=False)
    poste_comptable: Mapped[str] = mapped_column(String(10), nullable=False)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_ht: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    montant_ht: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tva_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    tva_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    montant_ttc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    visible_on_print: Mapped[bool] = mapped_column(default=True)
    source_service: Mapped[str | None] = mapped_column(String(50))
    catalog_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    correction_of: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("folio_charges.id"))
    corrects_date: Mapped[date_type | None] = mapped_column(Date)
    correction_reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    business_date: Mapped[date_type] = mapped_column(Date, nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_folio_charges_quantity_positive"),
        CheckConstraint("tva_rate IN (0,10,20)", name="chk_folio_charges_tva_rate"),
        CheckConstraint(
            "poste_comptable IN ('HEB','PDJ','RES','BAR','SPA','ACT','TS','TPT','REM','HAM','TRF','DIN','EXC')",
            name="chk_folio_charges_poste",
        ),
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    folio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("folios.id"), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    montant: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))
    encaisse_par: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    encaisse_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    business_date: Mapped[date_type] = mapped_column(Date, nullable=False)

    __table_args__ = (
        CheckConstraint("mode IN ('CB','ESP','CHQ','Virement','Débiteur')", name="chk_payments_mode"),
        CheckConstraint("montant > 0", name="chk_payments_montant_positive"),
    )


class BusinessDateLock(Base):
    __tablename__ = "business_date_locks"

    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    business_date: Mapped[date_type] = mapped_column(Date, primary_key=True)
    is_locked: Mapped[bool] = mapped_column(default=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    audit_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
