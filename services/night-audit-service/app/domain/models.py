"""Transcription littérale du spec §5.6 (lignes 1188-1227) : audit_runs,
system_state, audit_snapshots.

Sprint 5 — schéma posé à l'avance, aucun endpoint n'existe encore."""

import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class AuditRun(Base):
    __tablename__ = "audit_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    business_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    total_debits: Mapped[float | None] = mapped_column(Numeric(14, 2))
    total_credits: Mapped[float | None] = mapped_column(Numeric(14, 2))
    discrepancy: Mapped[float | None] = mapped_column(Numeric(14, 2))
    closed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    report_urls: Mapped[dict | None] = mapped_column(JSONB)
    report_hash: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','balancing','balanced','error','closed')", name="chk_audit_runs_status"
        ),
        UniqueConstraint("establishment_id", "business_date", name="uq_audit_runs_establishment_date"),
    )


class SystemState(Base):
    __tablename__ = "system_state"

    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    business_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    last_audit_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("audit_runs.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditSnapshot(Base):
    __tablename__ = "audit_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    business_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    service_name: Mapped[str] = mapped_column(String(50), nullable=False)
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "establishment_id", "business_date", "service_name", name="uq_audit_snapshots_establishment_date_service"
        ),
    )
