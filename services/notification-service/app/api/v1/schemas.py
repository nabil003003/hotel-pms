import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Rôles réels du realm Keycloak (scripts/keycloak_setup.py::REALM_ROLES) —
# seuls destinataires valides pour un message humain (pas de rôle "client",
# qui n'est qu'une étiquette utilisée pour l'email de remerciement, D11).
STAFF_ROLES = Literal[
    "femme_de_chambre", "gouvernante", "receptionniste", "manager", "admin", "comptable", "agence_externe"
]


class NotificationSendIn(BaseModel):
    establishment_id: uuid.UUID
    event_type: str
    channel: str = Field(pattern="^(email|push|sms|message)$")
    recipient_role: str
    subject: str
    body: str
    related_entity_id: uuid.UUID | None = None
    payload: dict | None = None


class MessageSendIn(BaseModel):
    """Message envoyé manuellement par un humain (manager/admin) à un rôle —
    distinct de `/send` (réservé aux comptes de service, D11) : ici
    l'expéditeur vient du token, jamais du corps de la requête, pour ne pas
    permettre d'usurper l'identité d'un autre utilisateur."""

    establishment_id: uuid.UUID
    recipient_role: STAFF_ROLES
    subject: str
    body: str


class NotificationOut(BaseModel):
    id: uuid.UUID
    establishment_id: uuid.UUID
    event_type: str
    channel: str
    recipient_role: str
    subject: str
    body: str
    status: str
    related_entity_id: uuid.UUID | None
    payload: dict
    created_at: datetime
    sent_at: datetime | None
    read_at: datetime | None

    model_config = {"from_attributes": True}
