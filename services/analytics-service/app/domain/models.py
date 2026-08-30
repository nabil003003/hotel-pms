"""Transcription littérale du spec §5.7 (lignes 1229-1290) : daily_kpi_snapshot,
monthly_kpi_aggregation, channel_performance.

La vue `kpi_ytd_comparison` (SQL pur, lignes 1276-1289) n'est pas modélisée en
ORM ici — elle sera créée par une migration Alembic dédiée (op.execute) au
Sprint 4, quand elle sera effectivement consommée par un endpoint.

`segment_id` rendu non-nullable (transcription littérale le voulait nullable
*et* membre de la clé primaire, invalide en Postgres — une colonne de PK ne
peut pas être NULL). Chaque ligne reste scopée à un `market_segment_id` réel
(celui de la réservation qui a déclenché l'écriture) ; les totaux "tous
segments" sont calculés par somme à la lecture plutôt que stockés comme une
ligne sentinelle.

Sprint 4 — schéma posé à l'avance, aucun endpoint n'existe encore."""

import uuid
from datetime import date as date_type

from sqlalchemy import Date, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class DailyKpiSnapshot(Base):
    __tablename__ = "daily_kpi_snapshot"

    business_date: Mapped[date_type] = mapped_column(Date, primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    segment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    nuitees: Mapped[int] = mapped_column(Integer, default=0)
    ca_brut: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    ca_ht: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    tva_total: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    to_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    adr: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    revpar: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    dms: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    pax_total: Mapped[int] = mapped_column(Integer, default=0)
    encaissements: Mapped[float] = mapped_column(Numeric(14, 2), default=0)


class MonthlyKpiAggregation(Base):
    __tablename__ = "monthly_kpi_aggregation"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[int] = mapped_column(Integer, primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    segment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    nuitees: Mapped[int] = mapped_column(Integer, default=0)
    ca_brut: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    to_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    adr: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    revpar: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    dms: Mapped[float] = mapped_column(Numeric(5, 2), default=0)


class ChannelPerformance(Base):
    __tablename__ = "channel_performance"

    business_date: Mapped[date_type] = mapped_column(Date, primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    channel: Mapped[str] = mapped_column(String(50), primary_key=True)
    bookings_count: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    commission: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    net_revenue: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
