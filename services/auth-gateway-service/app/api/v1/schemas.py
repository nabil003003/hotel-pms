import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class MeOut(BaseModel):
    sub: str
    roles: list[str]
    establishment_ids: list[str]
    is_super_admin: bool
    webauthn_linked: bool


class UserCreateIn(BaseModel):
    username: str
    email: EmailStr
    role: str
    establishment_ids: list[uuid.UUID]
    is_super_admin: bool = False


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    is_super_admin: bool
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreateOut(BaseModel):
    user: UserOut
    temp_password: str


class EstablishmentUserOut(BaseModel):
    """Utilisateur dans le contexte d'un établissement — inclut le rôle et la
    date d'entrée dans CET établissement (`user_establishments`), à la
    différence de `UserOut` qui décrit le compte seul, sans contexte."""

    id: uuid.UUID
    email: str
    display_name: str | None
    is_active: bool
    role: str
    created_at: datetime
    temp_password: str | None = None

    model_config = {"from_attributes": True}


class UserRoleUpdateIn(BaseModel):
    role: str


class ElevateIn(BaseModel):
    establishment_id: uuid.UUID


class ElevateOut(BaseModel):
    token: str
    expires_at: str


class ElevateConsumeIn(BaseModel):
    token: str


class ElevateConsumeOut(BaseModel):
    user_id: uuid.UUID
    establishment_id: uuid.UUID


class PhoneLinkBeginOut(BaseModel):
    token: str
    expires_at: str


class PhoneLinkStatusOut(BaseModel):
    status: str


class LoginLinkBeginOut(BaseModel):
    token: str
    expires_at: str


class LoginLinkStatusOut(BaseModel):
    status: str


class LoginLinkCompleteIn(BaseModel):
    refresh_token: str | None = None
    id_token: str | None = None


class LoginLinkClaimOut(BaseModel):
    access_token: str | None
    refresh_token: str | None
    id_token: str | None


class AuditLogEntryOut(BaseModel):
    """Ligne de auth_audit_log — miroir d'un event LOGIN/LOGIN_ERROR
    Keycloak (biom.txt), peuplé par app/infrastructure/audit_poller.py."""

    id: uuid.UUID
    user_id: uuid.UUID | None
    email: str | None
    event_type: str
    error: str | None
    ip_address: str | None
    occurred_at: datetime

    model_config = {"from_attributes": True}
