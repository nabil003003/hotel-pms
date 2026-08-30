"""Transcription littérale du spec §5.1 (lignes 758-825) :
establishments, rooms, establishment_services, ota_mappings."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class Establishment(Base):
    __tablename__ = "establishments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str] = mapped_column(String(100), default="Marrakech")
    country: Mapped[str] = mapped_column(String(100), default="Maroc")
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    total_rooms: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (CheckConstraint("total_rooms > 0", name="chk_total_rooms_positive"),)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    establishment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("establishments.id"), nullable=False
    )
    numero: Mapped[str] = mapped_column(String(10), nullable=False)
    categorie: Mapped[str] = mapped_column(String(50), nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity_adults: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    capacity_children: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text)
    amenities: Mapped[list] = mapped_column(JSONB, default=list)
    photos: Mapped[list] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("establishment_id", "numero", name="uq_rooms_establishment_numero"),)


# Taxonomie canonique des catégories (D5) — utilisée pour la validation
# applicative en plus du champ libre `categorie` (le spec le laisse en
# VARCHAR libre, mais Workflow K liste ces 5 valeurs comme référence).
CANONICAL_ROOM_CATEGORIES = [
    "Chambre Standard",
    "Chambre Deluxe",
    "Suite Junior",
    "Suite Royale",
    "Riad Entier",
]


# Doit rester synchronisé avec le CheckConstraint chk_establishment_services_category
# ci-dessous — utilisée pour valider en amont côté applicatif (422 propre) plutôt
# que de laisser remonter un CheckViolation Postgres non catché (500).
CANONICAL_SERVICE_CATEGORIES = ["Hammam", "Transfert", "Excursion", "Diner", "Cours_Cuisine", "Autre"]


class EstablishmentService(Base):
    __tablename__ = "establishment_services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    establishment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("establishments.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    prix_ht: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tva_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=20.00)
    prix_ttc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "category IN ('Hammam','Transfert','Excursion','Diner','Cours_Cuisine','Autre')",
            name="chk_establishment_services_category",
        ),
    )


class OtaMapping(Base):
    """Table créée pour fidélité au schéma (§5.1) mais SANS endpoint exposé en
    Sprint 1 — le spec se contredit sur l'ownership de cette table entre
    establishment-service (§5.1) et channel-manager-service (Workflow C/K).
    Décision D3 (plan Sprint 1) : trancher au Sprint 2."""

    __tablename__ = "ota_mappings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    establishment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("establishments.id"), nullable=False
    )
    ota_name: Mapped[str] = mapped_column(String(50), nullable=False)
    ota_property_id: Mapped[str] = mapped_column(String(100), nullable=False)
    ota_room_type_id: Mapped[str | None] = mapped_column(String(100))
    internal_room_category: Mapped[str | None] = mapped_column(String(50))
    credentials_encrypted: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "ota_name IN ('booking_com','expedia','airbnb','direct_website')",
            name="chk_ota_mappings_name",
        ),
        UniqueConstraint(
            "establishment_id", "ota_name", "ota_room_type_id", name="uq_ota_mappings_establishment_name_room"
        ),
    )
