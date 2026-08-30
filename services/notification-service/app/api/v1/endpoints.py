import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    CurrentUser,
    assert_path_establishment_access,
    get_current_user,
    get_db,
    require_roles,
    require_super_admin,
)
from app.domain.exceptions import NotificationNotFoundError
from app.domain.services import (
    create_notification,
    get_notification,
    list_my_notifications,
    list_notifications,
    mark_notification_read,
)

from .schemas import MessageSendIn, NotificationOut, NotificationSendIn

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

# Qui peut envoyer un message manuel — mêmes rôles que ceux habilités à piloter
# la clôture night-audit (encadrement), pas le personnel de terrain.
MESSAGE_SENDER_ROLES = ("manager", "admin")


@router.post("/send", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
async def send_notification_endpoint(
    body: NotificationSendIn,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
) -> NotificationOut:
    """Appel direct synchrone (D11/D12) — utilisé par night-audit-service pour
    l'alerte d'écart pré-audit et l'email de rapport post-audit, deux cas où
    le payload transporté dépasse ce que `audit.closed` porte dans
    l'Appendix C. Réservé aux comptes de service (`is_super_admin`)."""
    notification = await create_notification(db, **body.model_dump())
    return NotificationOut.model_validate(notification)


@router.post("/message", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
async def send_message_endpoint(
    body: MessageSendIn,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_roles(*MESSAGE_SENDER_ROLES)),
) -> NotificationOut:
    """Message manuel d'un humain vers un rôle — l'expéditeur vient
    toujours du token (`user.sub`/`user.email`), jamais du corps de la
    requête, pour ne pas permettre d'usurper l'identité d'un autre
    utilisateur (cf. docstring MessageSendIn)."""
    assert_path_establishment_access(user, body.establishment_id)
    notification = await create_notification(
        db,
        establishment_id=body.establishment_id,
        event_type="message.direct",
        channel="message",
        recipient_role=body.recipient_role,
        subject=body.subject,
        body=body.body,
        payload={"sender_sub": user.sub, "sender_email": user.email},
    )
    return NotificationOut.model_validate(notification)


@router.get("/mine", response_model=list[NotificationOut])
async def read_my_notifications_endpoint(
    establishment_id: uuid.UUID,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[NotificationOut]:
    """Scopé aux rôles de l'appelant — alimente la cloche du topbar (badge
    non-lus + liste), séparé de `GET /` qui liste tout l'établissement pour
    la page Notifications (D11)."""
    assert_path_establishment_access(user, establishment_id)
    roles = list(user.roles) if not user.is_super_admin else [
        "femme_de_chambre", "gouvernante", "receptionniste", "manager", "admin", "comptable", "agence_externe",
    ]
    notifications = await list_my_notifications(db, establishment_id, recipient_roles=roles, unread_only=unread_only)
    return [NotificationOut.model_validate(n) for n in notifications]


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read_endpoint(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> NotificationOut:
    try:
        notification = await get_notification(db, notification_id)
    except NotificationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, notification.establishment_id)
    if not user.is_super_admin and notification.recipient_role not in user.roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not addressed to your role")
    notification = await mark_notification_read(db, notification_id)
    return NotificationOut.model_validate(notification)


@router.get("", response_model=list[NotificationOut])
async def read_notifications(
    establishment_id: uuid.UUID,
    event_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[NotificationOut]:
    assert_path_establishment_access(user, establishment_id)
    notifications = await list_notifications(db, establishment_id, event_type=event_type)
    return [NotificationOut.model_validate(n) for n in notifications]


@router.get("/{notification_id}", response_model=NotificationOut)
async def read_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> NotificationOut:
    try:
        notification = await get_notification(db, notification_id)
    except NotificationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    assert_path_establishment_access(user, notification.establishment_id)
    return NotificationOut.model_validate(notification)
