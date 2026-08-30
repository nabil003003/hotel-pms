"""Schéma auth_db — non fourni littéralement par le spec (seuls §5.1-5.8 le
sont). Conçu à partir de §3.4 (table `user_establishments` many-to-many
explicitement requise) — voir plan Sprint 1, décision D1/auth-gateway."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


class User(Base):
    """Cache local du profil Keycloak — id = `sub` du JWT. Évite un aller-
    retour vers l'Admin API Keycloak à chaque requête pour l'affichage."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Effacé dès que Keycloak confirme que le required action UPDATE_PASSWORD
    # a été rempli (l'utilisateur a changé son mot de passe temporaire) —
    # permet à un admin de le réafficher tant que ce n'est pas encore fait.
    temp_password: Mapped[str | None] = mapped_column(String(255))
    # Vrai une fois le flow /link-phone (biom.txt Flux A) complété avec
    # succès — piloté par notre propre relais QR, pas par les required
    # actions Keycloak (le navigateur natif s'est montré peu fiable selon
    # l'appareil, voir PhoneLinkSession).
    webauthn_linked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    establishments: Mapped[list["UserEstablishment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserEstablishment(Base):
    """Many-to-many utilisateur <-> établissement (§3.4). Le `role` ici est un
    libellé de confort pour l'affichage admin ; la source de vérité RBAC reste
    le rôle réaliste Keycloak porté par le JWT (`realm_access.roles`)."""

    __tablename__ = "user_establishments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="establishments")


class ElevationSession(Base):
    """Scaffold Sprint 1, consommé à partir du Sprint 3 (Workflow F — upsell /
    room shifting nécessitant une ré-authentification manager/admin)."""

    __tablename__ = "elevation_sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    establishment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuthAuditLog(Base):
    """Miroir local des events LOGIN/LOGIN_ERROR de l'API Admin Events
    Keycloak (biom.txt) — peuplé par app/infrastructure/audit_poller.py, pas
    de FK vers `users` (voir migration 0003)."""

    __tablename__ = "auth_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    email: Mapped[str | None] = mapped_column(String(255))
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    error: Mapped[str | None] = mapped_column(String(100))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    session_id: Mapped[str | None] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    keycloak_event_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PhoneLinkSession(Base):
    """Relais QR desktop <-> téléphone (biom.txt Flux A) : le desktop crée un
    token borné à son propre user_id, l'affiche en QR vers /auth/hybrid?token=,
    et poll le status. Le téléphone se logge lui-même (même compte) et
    enregistre son propre credential WebAuthn same-device (pas de transport
    hybride/Bluetooth requis), puis marque la session "completed" — le
    desktop détecte le changement et se relogue silencieusement via SSO."""

    __tablename__ = "phone_link_sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LoginLinkSession(Base):
    """Relais QR login (biom.txt Flux B) — contrairement à PhoneLinkSession,
    le desktop n'est PAS encore authentifié quand il génère le QR : on ne
    connaît le user qu'une fois le téléphone loggé. Le téléphone dépose ses
    3 tokens OIDC ici (le backend ne voit jamais que l'access_token via
    Authorization, refresh/id_token transitent en body — seul le frontend
    Next.js les détient normalement, cf. lib/auth/cookies.ts), le desktop
    les récupère une seule fois (`claimed_at`) puis ils sont effacés."""

    __tablename__ = "login_link_sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    access_token: Mapped[str | None] = mapped_column(Text())
    refresh_token: Mapped[str | None] = mapped_column(Text())
    id_token: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
