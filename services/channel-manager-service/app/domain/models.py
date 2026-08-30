"""Schéma propre à channel-manager-service (pas de transcription §5.x — le
spec ne définit aucune table pour ce service, cf. D3). `ota_mappings` reste
dans establishment_db (D3, option 1) ; ce service possède seulement l'état
de connexion OTA et le journal de synchronisation."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base

OTA_NAMES = "'booking_com','expedia','airbnb','direct_website'"


class ChannelConnection(Base):
    __tablename__ = "channel_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ota_name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    credentials_encrypted: Mapped[str | None] = mapped_column(Text)
    two_way_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(f"ota_name IN ({OTA_NAMES})", name="chk_channel_connections_ota_name"),
        UniqueConstraint("establishment_id", "ota_name", name="uq_channel_connections_establishment_ota"),
    )


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ota_name: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('ok','error','buffered')", name="chk_sync_logs_status"),
    )
