"""Transcription littérale du spec §5.4 (lignes 1034-1102) :
rooms (copie locale de establishment-service, D1), room_status_history,
room_planning (créée maintenant, utilisée à partir du Sprint 3),
room_incidents."""

import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base

ROOM_STATUSES = ["Sale", "Nettoyage", "Propre", "Contrôlée", "Bloquée"]

# Transcrit tel quel de la CHECK constraint §5.4 ligne 1043-1045. Note : le
# PDF Module 2 original et housekeeping.html utilisent le libellé d'affichage
# "Problème technique" — le code stable en base reste 'Panne' (fidélité au
# schéma littéral du spec, la traduction d'affichage se fait côté frontend).
BLOCK_REASONS = ["Day Use", "Panne", "Départ tardif", "Travaux"]

INCIDENT_TYPES = ["Panne technique", "Manque de linge", "Problème sanitaire", "Autre"]

# Machine à états stricte (Workflow H §4.8) : exactement ces 5 transitions,
# toute autre paire -> 409 INVALID_TRANSITION.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "Sale": {"Nettoyage"},
    "Nettoyage": {"Propre"},
    "Propre": {"Contrôlée"},
    "Contrôlée": {"Bloquée"},
    "Bloquée": {"Propre"},
}


class Room(Base):
    """Copie locale des chambres, maintenue par les événements
    `establishment.*` consommés dans events/consumer.py (décision D1) —
    establishment-service reste la source de vérité pour numero/categorie/floor."""

    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    numero: Mapped[str] = mapped_column(String(10), nullable=False)
    categorie: Mapped[str] = mapped_column(String(50), nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="Propre")
    motif_blocage: Mapped[str | None] = mapped_column(String(20))
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    blocked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    blocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("statut IN ('Sale','Nettoyage','Propre','Contrôlée','Bloquée')", name="chk_rooms_statut"),
        CheckConstraint(
            "motif_blocage IS NULL OR motif_blocage IN ('Day Use','Panne','Départ tardif','Travaux')",
            name="chk_rooms_motif_blocage",
        ),
        UniqueConstraint("establishment_id", "numero", name="uq_hk_rooms_establishment_numero"),
    )


class RoomStatusHistory(Base):
    __tablename__ = "room_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reason: Mapped[str | None] = mapped_column(Text)


class RoomPlanning(Base):
    """Créée en Sprint 1 pour fidélité au schéma, activée au Sprint 3
    (reservation-service). Aucun endpoint ne l'exploite avant."""

    __tablename__ = "room_planning"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (UniqueConstraint("establishment_id", "room_id", "date", name="uq_planning_establishment_room_date"),)


class RoomIncident(Base):
    __tablename__ = "room_incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    photo_url: Mapped[str | None] = mapped_column(String(500))
    reported_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    __table_args__ = (
        CheckConstraint(
            "incident_type IN ('Panne technique','Manque de linge','Problème sanitaire','Autre')",
            name="chk_incidents_type",
        ),
    )
