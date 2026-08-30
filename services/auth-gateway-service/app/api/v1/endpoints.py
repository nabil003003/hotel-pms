import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    CurrentUser,
    assert_path_establishment_access,
    bearer_scheme,
    get_current_user,
    get_db,
    require_roles,
)
from app.domain.exceptions import (
    ElevationSessionInvalidError,
    LoginLinkSessionInvalidError,
    PhoneLinkSessionInvalidError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.domain.services import (
    claim_login_link_session,
    complete_login_link_session,
    complete_phone_link_session,
    consume_elevation_session,
    create_elevation_session,
    create_login_link_session,
    create_phone_link_session,
    deactivate_establishment_user,
    delete_establishment_user_permanently,
    ensure_user_cached,
    get_login_link_session,
    get_phone_link_session,
    list_audit_log_for_establishment,
    list_users_for_establishment,
    provision_user,
    update_establishment_user_role,
)

from .schemas import (
    AuditLogEntryOut,
    ElevateConsumeIn,
    ElevateConsumeOut,
    ElevateIn,
    ElevateOut,
    EstablishmentUserOut,
    LoginLinkBeginOut,
    LoginLinkClaimOut,
    LoginLinkCompleteIn,
    LoginLinkStatusOut,
    MeOut,
    PhoneLinkBeginOut,
    PhoneLinkStatusOut,
    UserCreateIn,
    UserCreateOut,
    UserOut,
    UserRoleUpdateIn,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/me", response_model=MeOut)
async def read_me(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> MeOut:
    cached = await ensure_user_cached(db, sub=user.sub, email=user.email, is_super_admin=user.is_super_admin)
    return MeOut(
        sub=user.sub,
        roles=user.roles,
        establishment_ids=user.establishment_ids,
        is_super_admin=user.is_super_admin,
        webauthn_linked=cached.webauthn_linked,
    )


@router.post("/users", response_model=UserCreateOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateIn,
    db: AsyncSession = Depends(get_db),
    caller: CurrentUser = Depends(require_roles("admin")),
) -> UserCreateOut:
    # Un "admin" est un rôle Keycloak global (pas de scoping par
    # établissement dans le JWT), donc sans ces deux garde-fous un admin créé
    # pour UN SEUL établissement pouvait : (1) se fabriquer un compte
    # is_super_admin=true — élévation de privilège complète — et (2) créer
    # des utilisateurs pour n'importe quel autre établissement en devinant
    # son UUID, pas seulement le sien. Bug réel remonté par l'utilisateur
    # ("un admin a les mêmes fonctionnalités qu'un super admin").
    if body.is_super_admin and not caller.is_super_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only a super-admin can create another super-admin")
    if not caller.is_super_admin:
        allowed = set(caller.establishment_ids)
        requested = {str(eid) for eid in body.establishment_ids}
        if not requested.issubset(allowed):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Cannot create a user for an establishment you don't manage"
            )

    try:
        user, temp_password = await provision_user(
            db,
            username=body.username,
            email=body.email,
            role=body.role,
            establishment_ids=body.establishment_ids,
            is_super_admin=body.is_super_admin,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    return UserCreateOut(user=UserOut.model_validate(user), temp_password=temp_password)


@router.get("/establishments/{establishment_id}/users", response_model=list[EstablishmentUserOut])
async def read_establishment_users(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("admin", "manager")),
) -> list[EstablishmentUserOut]:
    assert_path_establishment_access(user, establishment_id)
    rows = await list_users_for_establishment(db, establishment_id)
    return [
        EstablishmentUserOut(
            id=user.id, email=user.email, display_name=user.display_name,
            is_active=user.is_active, role=membership.role, created_at=membership.created_at,
            temp_password=user.temp_password,
        )
        for user, membership in rows
    ]


@router.patch("/establishments/{establishment_id}/users/{user_id}", response_model=EstablishmentUserOut)
async def update_establishment_user(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    body: UserRoleUpdateIn,
    db: AsyncSession = Depends(get_db),
    caller: CurrentUser = Depends(require_roles("admin")),
) -> EstablishmentUserOut:
    assert_path_establishment_access(caller, establishment_id)
    try:
        user, membership = await update_establishment_user_role(db, establishment_id, user_id, body.role)
    except UserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return EstablishmentUserOut(
        id=user.id, email=user.email, display_name=user.display_name,
        is_active=user.is_active, role=membership.role, created_at=membership.created_at,
        temp_password=user.temp_password,
    )


@router.delete("/establishments/{establishment_id}/users/{user_id}", response_model=EstablishmentUserOut)
async def delete_establishment_user(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    caller: CurrentUser = Depends(require_roles("admin")),
) -> EstablishmentUserOut:
    assert_path_establishment_access(caller, establishment_id)
    try:
        user, membership = await deactivate_establishment_user(db, establishment_id, user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return EstablishmentUserOut(
        id=user.id, email=user.email, display_name=user.display_name,
        is_active=user.is_active, role=membership.role, created_at=membership.created_at,
        temp_password=user.temp_password,
    )


@router.delete(
    "/establishments/{establishment_id}/users/{user_id}/permanent", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_establishment_user_permanently_route(
    establishment_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    caller: CurrentUser = Depends(require_roles("admin")),
) -> None:
    """Suppression définitive — irréversible, distincte du DELETE ci-dessus
    (qui désactive seulement). Retire le compte de Keycloak et de la base
    locale, sans laisser de trace. Idempotente (voir docstring du domain
    service) : un compte déjà supprimé renvoie 204 comme un premier succès."""
    assert_path_establishment_access(caller, establishment_id)
    await delete_establishment_user_permanently(db, establishment_id, user_id)


@router.get("/establishments/{establishment_id}/audit-log", response_model=list[AuditLogEntryOut])
async def read_audit_log(
    establishment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    caller: CurrentUser = Depends(require_roles("admin", "manager")),
) -> list[AuditLogEntryOut]:
    """Journal de connexion (biom.txt) — miroir des events Keycloak LOGIN/
    LOGIN_ERROR peuplé par app/infrastructure/audit_poller.py."""
    assert_path_establishment_access(caller, establishment_id)
    rows = await list_audit_log_for_establishment(db, establishment_id)
    return [AuditLogEntryOut.model_validate(row) for row in rows]


@router.post("/phone-link/begin", response_model=PhoneLinkBeginOut)
async def phone_link_begin(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
) -> PhoneLinkBeginOut:
    """Desktop authentifié démarre une session de liaison téléphone (biom.txt
    Flux A, page /link-phone) — le token est ensuite encodé en QR vers
    /auth/hybrid?token=... pour que le téléphone le complète lui-même."""
    await ensure_user_cached(db, sub=user.sub, email=user.email, is_super_admin=user.is_super_admin)
    session = await create_phone_link_session(db, user_id=uuid.UUID(user.sub))
    return PhoneLinkBeginOut(token=session.token, expires_at=session.expires_at.isoformat())


@router.get("/phone-link/{token}/status", response_model=PhoneLinkStatusOut)
async def phone_link_status(token: str, db: AsyncSession = Depends(get_db)) -> PhoneLinkStatusOut:
    """Pollé par la page desktop — pas d'auth requise, le token fait office
    de capability (32 octets aléatoires, cf. create_phone_link_session)."""
    try:
        session = await get_phone_link_session(db, token=token)
    except PhoneLinkSessionInvalidError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown phone link token")
    return PhoneLinkStatusOut(status=session.status)


@router.post("/phone-link/{token}/complete", response_model=PhoneLinkStatusOut)
async def phone_link_complete(
    token: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> PhoneLinkStatusOut:
    """Appelé par le téléphone (son propre JWT, obtenu après avoir loggé et
    enregistré son credential WebAuthn same-device) — refuse si le compte ne
    correspond pas à celui qui a démarré la session côté desktop."""
    try:
        session = await complete_phone_link_session(db, token=token, user_id=uuid.UUID(user.sub))
    except PhoneLinkSessionInvalidError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return PhoneLinkStatusOut(status=session.status)


@router.post("/login-link/begin", response_model=LoginLinkBeginOut)
async def login_link_begin(db: AsyncSession = Depends(get_db)) -> LoginLinkBeginOut:
    """Pas d'auth requise : le desktop n'est PAS encore connecté quand il
    affiche ce QR sur /login (biom.txt Flux B)."""
    session = await create_login_link_session(db)
    return LoginLinkBeginOut(token=session.token, expires_at=session.expires_at.isoformat())


@router.get("/login-link/{token}/status", response_model=LoginLinkStatusOut)
async def login_link_status(token: str, db: AsyncSession = Depends(get_db)) -> LoginLinkStatusOut:
    try:
        session = await get_login_link_session(db, token=token)
    except LoginLinkSessionInvalidError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown login link token")
    return LoginLinkStatusOut(status=session.status)


@router.post("/login-link/{token}/complete", response_model=LoginLinkStatusOut)
async def login_link_complete(
    token: str,
    body: LoginLinkCompleteIn,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    _: CurrentUser = Depends(get_current_user),
) -> LoginLinkStatusOut:
    """Appelé par le téléphone juste après son propre login — dépose ses 3
    tokens OIDC pour que le desktop les récupère (une seule fois, cf.
    /claim). `_: CurrentUser` valide juste que le bearer est un JWT légitime
    avant d'accepter quoi que ce soit."""
    try:
        session = await complete_login_link_session(
            db,
            token=token,
            access_token=credentials.credentials,
            refresh_token=body.refresh_token,
            id_token=body.id_token,
        )
    except LoginLinkSessionInvalidError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return LoginLinkStatusOut(status=session.status)


@router.post("/login-link/{token}/claim", response_model=LoginLinkClaimOut)
async def login_link_claim(token: str, db: AsyncSession = Depends(get_db)) -> LoginLinkClaimOut:
    """Pas d'auth requise (le desktop n'est justement pas encore connecté) —
    le token à usage unique fait office de capability. Efface les tokens en
    base immédiatement après lecture (voir claim_login_link_session)."""
    try:
        claimed = await claim_login_link_session(db, token=token)
    except LoginLinkSessionInvalidError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return LoginLinkClaimOut(
        access_token=claimed.access_token, refresh_token=claimed.refresh_token, id_token=claimed.id_token
    )


@router.post("/elevate", response_model=ElevateOut)
async def elevate(
    body: ElevateIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles("manager", "admin")),
) -> ElevateOut:
    """Scaffold Sprint 1 : émet une session d'élévation. Non consommé par
    aucun autre service avant le Sprint 3 (room shifting / upsell)."""
    await ensure_user_cached(db, sub=user.sub, email=user.email, is_super_admin=user.is_super_admin)
    session = await create_elevation_session(
        db, user_id=uuid.UUID(user.sub), establishment_id=body.establishment_id
    )
    return ElevateOut(token=session.token, expires_at=session.expires_at.isoformat())


@router.post("/elevate/consume", response_model=ElevateConsumeOut)
async def elevate_consume(
    body: ElevateConsumeIn,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> ElevateConsumeOut:
    """Sprint 3 : appelé par reservation-service (compte de service) pour
    valider et consommer (usage unique) un token émis par `/elevate` avant
    d'autoriser un room-shift upsell (décision D8)."""
    try:
        session = await consume_elevation_session(db, token=body.token)
    except ElevationSessionInvalidError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    return ElevateConsumeOut(user_id=session.user_id, establishment_id=session.establishment_id)
