"""Transcription littérale du spec §5.5 (lignes 1104-1186) : seasons,
rate_grid, taxes_config, extras_catalog, partner_rates, packages.

Sprint 2 — schéma posé à l'avance, aucun endpoint n'existe encore (voir
app/api/v1/endpoints.py)."""

import uuid
from datetime import date as date_type

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    date_debut: Mapped[date_type] = mapped_column(Date, nullable=False)
    date_fin: Mapped[date_type] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (CheckConstraint("date_fin > date_debut", name="chk_season_dates"),)


class RateGrid(Base):
    __tablename__ = "rate_grid"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_category: Mapped[str] = mapped_column(String(50), nullable=False)
    season_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False)
    regime: Mapped[str] = mapped_column(String(5), nullable=False)
    prix_ttc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    prix_ht: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tva_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=10.00)

    __table_args__ = (
        CheckConstraint("regime IN ('BB','DP','PC')", name="chk_rate_grid_regime"),
        CheckConstraint("prix_ttc > 0", name="chk_rate_grid_prix_positive"),
        UniqueConstraint("establishment_id", "room_category", "season_id", "regime", name="uq_rate_grid"),
    )


class TaxConfig(Base):
    __tablename__ = "taxes_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    taux_ou_montant: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    mode_calcul: Mapped[str] = mapped_column(String(20), nullable=False)
    applicable_from: Mapped[date_type] = mapped_column(Date, nullable=False, default=date_type(2024, 1, 1))
    applicable_to: Mapped[date_type | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        CheckConstraint("type IN ('TVA_HEBERGEMENT','TVA_AUTRE','TS','TPT')", name="chk_taxes_type"),
        CheckConstraint("mode_calcul IN ('PERCENTAGE','FIXED_PER_PAX')", name="chk_taxes_mode_calcul"),
    )


class ExtrasCatalogItem(Base):
    __tablename__ = "extras_catalog"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    categorie: Mapped[str] = mapped_column(String(20), nullable=False)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    prix_ht: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tva_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=20.00)
    prix_ttc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        CheckConstraint(
            "categorie IN ('Restaurant','Bar','SPA','Activités','Autre')", name="chk_extras_categorie"
        ),
    )


class PartnerRate(Base):
    __tablename__ = "partner_rates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    season_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False)
    room_category: Mapped[str] = mapped_column(String(50), nullable=False)
    regime: Mapped[str] = mapped_column(String(5), nullable=False)
    tarif_negocie: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    commission_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    __table_args__ = (
        UniqueConstraint(
            "establishment_id", "partner_id", "season_id", "room_category", "regime", name="uq_partner_rates"
        ),
    )


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    prix_global_ttc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    ventilation: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    valid_from: Mapped[date_type | None] = mapped_column(Date)
    valid_to: Mapped[date_type | None] = mapped_column(Date)
