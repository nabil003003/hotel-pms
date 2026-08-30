from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import (
    ElevationSessionInvalidError,
    LoginLinkSessionInvalidError,
    PhoneLinkSessionInvalidError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.domain.models import (
    AuthAuditLog,
    ElevationSession,
    LoginLinkSession,
    PhoneLinkSession,
    User,
    UserEstablishment,
)
from app.infrastructure.keycloak import keycloak_admin

ELEVATION_SESSION_TTL_MINUTES = 15
PHONE_LINK_SESSION_TTL_MINUTES = 5
# biom.txt §Flux B : "QR non scanné dans 2 min -> login email/password".
LOGIN_LINK_SESSION_TTL_MINUTES = 2


async def provision_user(
    db: AsyncSession,
    *,
    username: str,
    email: str,
    role: str,
    establishment_ids: list[uuid.UUID],
    is_super_admin: bool = False,
) -> tuple[User, str]:
    """Crée l'utilisateur dans Keycloak puis met à jour le cache local.
    Retourne (user, temp_password) pour transmission hors-bande à l'utilisateur."""
    existing = await db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise UserAlreadyExistsError(f"User already provisioned locally: {email}")

    temp_password = secrets.token_urlsafe(12)
    keycloak_sub = await keycloak_admin.create_user(
        username=username,
        email=email,
        temp_password=temp_password,
        realm_role=role,
        establishment_ids=[str(eid) for eid in establishment_ids],
        is_super_admin=is_super_admin,
    )

    user = User(
        id=uuid.UUID(keycloak_sub),
        email=email,
        display_name=username,
        is_super_admin=is_super_admin,
        is_active=True,
        temp_password=temp_password,
    )
    db.add(user)
    for establishment_id in establishment_ids:
        db.add(UserEstablishment(user_id=user.id, establishment_id=establishment_id, role=role))

    await db.commit()
    await db.refresh(user)
    return user, temp_password


async def ensure_user_cached(
    db: AsyncSession, *, sub: str, email: str | None, is_super_admin: bool
) -> User:
    """Upsert paresseux du cache local `users` à partir des claims JWT.
    Nécessaire car `elevation_sessions.user_id` a une FK vers `users.id` — un
    utilisateur peut légitimement appeler l'API avant tout provisioning
    explicite via POST /users (ex: comptes créés à la main dans Keycloak)."""
    user = await db.get(User, uuid.UUID(sub))
    if user is not None:
        return user

    user = User(
        id=uuid.UUID(sub),
        email=email or f"{sub}@unknown.local",
        is_super_admin=is_super_admin,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def list_users_for_establishment(
    db: AsyncSession, establishment_id: uuid.UUID
) -> list[tuple[User, UserEstablishment]]:
    stmt = (
        select(User, UserEstablishment)
        .join(UserEstablishment, UserEstablishment.user_id == User.id)
        .where(UserEstablishment.establishment_id == establishment_id)
    )
    result = await db.execute(stmt)
    rows = [(row.User, row.UserEstablishment) for row in result.all()]

    # Le mot de passe temporaire n'a de sens à réafficher que tant que
    # Keycloak indique que UPDATE_PASSWORD est toujours en attente — une fois
    # rempli (premier login), on l'efface localement (plus jamais valide).
    for user, _ in rows:
        if user.temp_password is None:
            continue
        required_actions = await keycloak_admin.get_required_actions(str(user.id))
        if "UPDATE_PASSWORD" not in required_actions:
            user.temp_password = None
    await db.commit()

    return rows


async def deactivate_establishment_user(
    db: AsyncSession, establishment_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[User, UserEstablishment]:
    """"Suppression" = désactivation réversible (cohérent avec le pattern
    "Désactiver" déjà utilisé pour les chambres) plutôt qu'un DELETE définitif
    — désactive le compte globalement (login refusé partout), pas seulement
    pour cet établissement, puisque `users.is_active` n'est pas scoping par
    établissement dans ce schéma."""
    user = await db.get(User, user_id)
    membership = await db.get(UserEstablishment, {"user_id": user_id, "establishment_id": establishment_id})
    if user is None or membership is None:
        raise UserNotFoundError(f"User {user_id} not linked to establishment {establishment_id}")

    user.is_active = False
    await keycloak_admin.set_user_enabled(str(user_id), False)
    await db.commit()
    await db.refresh(user)
    await db.refresh(membership)
    return user, membership


async def update_establishment_user_role(
    db: AsyncSession, establishment_id: uuid.UUID, user_id: uuid.UUID, new_role: str
) -> tuple[User, UserEstablishment]:
    user = await db.get(User, user_id)
    membership = await db.get(UserEstablishment, {"user_id": user_id, "establishment_id": establishment_id})
    if user is None or membership is None:
        raise UserNotFoundError(f"User {user_id} not linked to establishment {establishment_id}")

    membership.role = new_role
    await keycloak_admin.set_user_role(str(user_id), new_role)
    await db.commit()
    await db.refresh(user)
    await db.refresh(membership)
    return user, membership


async def delete_establishment_user_permanently(
    db: AsyncSession, establishment_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Suppression définitive et irréversible — Keycloak + toutes les traces
    locales (le compte n'est pas cantonné à un seul établissement dans le
    schéma : `User.establishments` cascade sur tous ses rattachements, pas
    seulement celui de `establishment_id`).

    Idempotente à dessein : si le compte ou son rattachement à cet
    établissement n'existe déjà plus (double-clic, re-essai après un premier
    succès, requête rejouée), on ne lève pas d'erreur — l'état voulu ("ce
    compte n'existe plus") est déjà atteint. Un DELETE qui échoue bruyamment
    sur sa propre réussite précédente est une source de confusion réelle,
    pas juste théorique (cf. capture d'écran D16 : retry sur une ligne déjà
    supprimée pris pour un bug du bouton Supprimer)."""
    user = await db.get(User, user_id)
    membership = await db.get(UserEstablishment, {"user_id": user_id, "establishment_id": establishment_id})
    if user is None or membership is None:
        return

    await keycloak_admin.delete_user(str(user_id))
    await db.execute(sa_delete(ElevationSession).where(ElevationSession.user_id == user_id))
    await db.delete(user)
    await db.commit()


async def list_audit_log_for_establishment(
    db: AsyncSession, establishment_id: uuid.UUID, *, limit: int = 200
) -> list[AuthAuditLog]:
    """Journal de connexion scopé établissement (biom.txt) — les events
    Keycloak n'ont pas de notion d'établissement, donc le scoping passe par
    une jointure sur `user_establishments`. Conséquence assumée : un event
    dont le userId ne résout à aucun utilisateur local connu (ex. tentative
    de login avec un identifiant inexistant) n'apparaît dans la vue d'AUCUN
    établissement — cohérent avec le reste du service, qui n'expose jamais
    de vue cross-tenant à un admin non super-admin."""
    stmt = (
        select(AuthAuditLog)
        .join(UserEstablishment, UserEstablishment.user_id == AuthAuditLog.user_id)
        .where(UserEstablishment.establishment_id == establishment_id)
        .order_by(AuthAuditLog.occurred_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_elevation_session(
    db: AsyncSession, *, user_id: uuid.UUID, establishment_id: uuid.UUID
) -> ElevationSession:
    """Scaffold — non consommé avant le Sprint 3 (room shifting / upsell)."""
    session = ElevationSession(
        token=secrets.token_hex(32),
        user_id=user_id,
        establishment_id=establishment_id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=ELEVATION_SESSION_TTL_MINUTES),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def consume_elevation_session(db: AsyncSession, *, token: str) -> ElevationSession:
    """Sprint 3 — consommé par reservation-service (room shifting / upsell,
    décision D8). Usage unique : `consumed_at` posé ici, toute réutilisation
    du même token échoue ensuite."""
    session = await db.get(ElevationSession, token)
    if session is None:
        raise ElevationSessionInvalidError("Unknown elevation token")
    if session.consumed_at is not None:
        raise ElevationSessionInvalidError("Elevation token already consumed")
    if session.expires_at < datetime.now(timezone.utc):
        raise ElevationSessionInvalidError("Elevation token expired")

    session.consumed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session


async def create_phone_link_session(db: AsyncSession, *, user_id: uuid.UUID) -> PhoneLinkSession:
    """Desktop authentifié -> QR /link-phone (biom.txt Flux A)."""
    session = PhoneLinkSession(
        token=secrets.token_urlsafe(32),
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=PHONE_LINK_SESSION_TTL_MINUTES),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_phone_link_session(db: AsyncSession, *, token: str) -> PhoneLinkSession:
    """Pollé par la page desktop — pas de garde d'auth ici (le token lui-même
    fait office de secret, comme les elevation sessions ci-dessus), mais ne
    révèle jamais rien de sensible (juste pending/completed/expired)."""
    session = await db.get(PhoneLinkSession, token)
    if session is None:
        raise PhoneLinkSessionInvalidError("Unknown phone link token")
    if session.status == "pending" and session.expires_at < datetime.now(timezone.utc):
        session.status = "expired"
        await db.commit()
        await db.refresh(session)
    return session


async def complete_phone_link_session(db: AsyncSession, *, token: str, user_id: uuid.UUID) -> PhoneLinkSession:
    """Appelé par le téléphone une fois son propre login + enregistrement
    WebAuthn same-device réussis. `user_id` doit correspondre à celui qui a
    initié la session côté desktop — empêche de compléter le QR de
    quelqu'un d'autre avec son propre compte."""
    session = await db.get(PhoneLinkSession, token)
    if session is None:
        raise PhoneLinkSessionInvalidError("Unknown phone link token")
    if session.status != "pending":
        raise PhoneLinkSessionInvalidError(f"Phone link session already {session.status}")
    if session.expires_at < datetime.now(timezone.utc):
        session.status = "expired"
        await db.commit()
        raise PhoneLinkSessionInvalidError("Phone link session expired")
    if session.user_id != user_id:
        raise PhoneLinkSessionInvalidError("Phone link session belongs to a different user")

    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)

    user = await db.get(User, user_id)
    if user is not None:
        user.webauthn_linked = True

    await db.commit()
    await db.refresh(session)
    return session


async def create_login_link_session(db: AsyncSession) -> LoginLinkSession:
    """Desktop PAS ENCORE authentifié -> QR sur /login (biom.txt Flux B)."""
    session = LoginLinkSession(
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=LOGIN_LINK_SESSION_TTL_MINUTES),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_login_link_session(db: AsyncSession, *, token: str) -> LoginLinkSession:
    session = await db.get(LoginLinkSession, token)
    if session is None:
        raise LoginLinkSessionInvalidError("Unknown login link token")
    if session.status == "pending" and session.expires_at < datetime.now(timezone.utc):
        session.status = "expired"
        await db.commit()
        await db.refresh(session)
    return session


async def complete_login_link_session(
    db: AsyncSession, *, token: str, access_token: str, refresh_token: str | None, id_token: str | None
) -> LoginLinkSession:
    """Le téléphone dépose ses tokens fraîchement obtenus — le desktop les
    récupérera une seule fois via claim_login_link_session ci-dessous."""
    session = await db.get(LoginLinkSession, token)
    if session is None:
        raise LoginLinkSessionInvalidError("Unknown login link token")
    if session.status != "pending":
        raise LoginLinkSessionInvalidError(f"Login link session already {session.status}")
    if session.expires_at < datetime.now(timezone.utc):
        session.status = "expired"
        await db.commit()
        raise LoginLinkSessionInvalidError("Login link session expired")

    session.access_token = access_token
    session.refresh_token = refresh_token
    session.id_token = id_token
    session.status = "completed"
    await db.commit()
    await db.refresh(session)
    return session


@dataclass
class ClaimedTokens:
    access_token: str | None
    refresh_token: str | None
    id_token: str | None


async def claim_login_link_session(db: AsyncSession, *, token: str) -> ClaimedTokens:
    """Le desktop récupère les tokens UNE SEULE FOIS — effacés immédiatement
    après (usage unique, comme un elevation token) pour ne jamais les
    laisser traîner en base plus longtemps que nécessaire."""
    session = await db.get(LoginLinkSession, token)
    if session is None:
        raise LoginLinkSessionInvalidError("Unknown login link token")
    if session.status != "completed":
        raise LoginLinkSessionInvalidError(f"Login link session not ready (status={session.status})")

    access_token, refresh_token, id_token = session.access_token, session.refresh_token, session.id_token
    session.access_token = None
    session.refresh_token = None
    session.id_token = None
    session.claimed_at = datetime.now(timezone.utc)
    await db.commit()

    return ClaimedTokens(access_token=access_token, refresh_token=refresh_token, id_token=id_token)
