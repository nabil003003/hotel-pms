"""initial schema — seasons, rate_grid, taxes_config, extras_catalog,
partner_rates, packages

Revision ID: 0001
Revises:
Create Date: 2026-07-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')

    op.create_table(
        "seasons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("date_debut", sa.Date(), nullable=False),
        sa.Column("date_fin", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.CheckConstraint("date_fin > date_debut", name="chk_season_dates"),
    )
    op.create_index("idx_seasons_establishment", "seasons", ["establishment_id"])

    op.create_table(
        "rate_grid",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_category", sa.String(50), nullable=False),
        sa.Column("season_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("seasons.id"), nullable=False),
        sa.Column("regime", sa.String(5), nullable=False),
        sa.Column("prix_ttc", sa.Numeric(12, 2), nullable=False),
        sa.Column("prix_ht", sa.Numeric(12, 2), nullable=False),
        sa.Column("tva_rate", sa.Numeric(5, 2), nullable=False, server_default="10.00"),
        sa.CheckConstraint("regime IN ('BB','DP','PC')", name="chk_rate_grid_regime"),
        sa.CheckConstraint("prix_ttc > 0", name="chk_rate_grid_prix_positive"),
        sa.UniqueConstraint(
            "establishment_id", "room_category", "season_id", "regime", name="uq_rate_grid"
        ),
    )
    op.create_index("idx_rate_grid_establishment", "rate_grid", ["establishment_id"])
    op.create_index("idx_rate_grid_season", "rate_grid", ["season_id"])

    op.create_table(
        "taxes_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("taux_ou_montant", sa.Numeric(12, 4), nullable=False),
        sa.Column("mode_calcul", sa.String(20), nullable=False),
        sa.Column("applicable_from", sa.Date(), nullable=False, server_default="2024-01-01"),
        sa.Column("applicable_to", sa.Date()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.CheckConstraint(
            "type IN ('TVA_HEBERGEMENT','TVA_AUTRE','TS','TPT')", name="chk_taxes_type"
        ),
        sa.CheckConstraint(
            "mode_calcul IN ('PERCENTAGE','FIXED_PER_PAX')", name="chk_taxes_mode_calcul"
        ),
    )
    op.create_index("idx_taxes_establishment", "taxes_config", ["establishment_id"])

    op.create_table(
        "extras_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("categorie", sa.String(20), nullable=False),
        sa.Column("libelle", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("prix_ht", sa.Numeric(12, 2), nullable=False),
        sa.Column("tva_rate", sa.Numeric(5, 2), nullable=False, server_default="20.00"),
        sa.Column("prix_ttc", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.CheckConstraint(
            "categorie IN ('Restaurant','Bar','SPA','Activités','Autre')", name="chk_extras_categorie"
        ),
    )
    op.create_index(
        "idx_extras_establishment", "extras_catalog", ["establishment_id"],
        postgresql_where=sa.text("is_active = TRUE"),
    )

    op.create_table(
        "partner_rates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("season_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("seasons.id"), nullable=False),
        sa.Column("room_category", sa.String(50), nullable=False),
        sa.Column("regime", sa.String(5), nullable=False),
        sa.Column("tarif_negocie", sa.Numeric(12, 2), nullable=False),
        sa.Column("commission_pct", sa.Numeric(5, 2), server_default="0"),
        sa.UniqueConstraint(
            "establishment_id", "partner_id", "season_id", "room_category", "regime", name="uq_partner_rates"
        ),
    )
    op.create_index("idx_partner_rates_partner", "partner_rates", ["establishment_id", "partner_id"])

    op.create_table(
        "packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("prix_global_ttc", sa.Numeric(12, 2), nullable=False),
        sa.Column("ventilation", postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("valid_from", sa.Date()),
        sa.Column("valid_to", sa.Date()),
    )
    op.create_index(
        "idx_packages_establishment", "packages", ["establishment_id"], postgresql_where=sa.text("is_active = TRUE")
    )


def downgrade() -> None:
    op.drop_index("idx_packages_establishment", table_name="packages")
    op.drop_table("packages")
    op.drop_index("idx_partner_rates_partner", table_name="partner_rates")
    op.drop_table("partner_rates")
    op.drop_index("idx_extras_establishment", table_name="extras_catalog")
    op.drop_table("extras_catalog")
    op.drop_index("idx_taxes_establishment", table_name="taxes_config")
    op.drop_table("taxes_config")
    op.drop_index("idx_rate_grid_season", table_name="rate_grid")
    op.drop_index("idx_rate_grid_establishment", table_name="rate_grid")
    op.drop_table("rate_grid")
    op.drop_index("idx_seasons_establishment", table_name="seasons")
    op.drop_table("seasons")
