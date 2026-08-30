"""Vérification JWT (JWKS Keycloak) + client Admin REST API.

Chaque microservice valide indépendamment les JWT contre le JWKS de Keycloak
(§3.5 du spec : pas de session partagée, pas de validation centralisée hors
Kong). Ce module est volontairement autonome et sans dépendance vers un autre
service — cohérent avec l'isolation microservices imposée par le spec.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from jose import jwt
from jose.exceptions import JWTError

from app.config import get_settings

settings = get_settings()

_jwks_cache: dict[str, Any] = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL_SECONDS = 300

# Rôles métier de l'app (cf. scripts/keycloak_setup.py:REALM_ROLES) — utilisé
# pour ne retirer que ces rôles-là lors d'un changement de poste, sans toucher
# à d'éventuels rôles techniques/Keycloak natifs de l'utilisateur.
APP_REALM_ROLES = [
    "femme_de_chambre",
    "gouvernante",
    "receptionniste",
    "manager",
    "admin",
    "comptable",
    "agence_externe",
]


async def _get_jwks() -> dict[str, Any]:
    now = time.time()
    if _jwks_cache["keys"] is None or now - _jwks_cache["fetched_at"] > _JWKS_TTL_SECONDS:
        url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            _jwks_cache["keys"] = resp.json()
            _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]


class TokenValidationError(Exception):
    pass


async def decode_access_token(token: str) -> dict[str, Any]:
    """Décode et valide un JWT Keycloak, retourne les claims."""
    jwks = await _get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise TokenValidationError("Malformed token header") from exc

    key = next((k for k in jwks.get("keys", []) if k.get("kid") == unverified_header.get("kid")), None)
    if key is None:
        # Le JWKS a pu tourner (rotation de clé) — on force un refresh une fois.
        _jwks_cache["keys"] = None
        jwks = await _get_jwks()
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == unverified_header.get("kid")), None)
        if key is None:
            raise TokenValidationError("Unknown signing key")

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=None,
            options={"verify_aud": False, "verify_iss": False},
        )
    except JWTError as exc:
        raise TokenValidationError(str(exc)) from exc

    expected_realm = f"/realms/{settings.keycloak_realm}"
    token_iss = claims.get("iss", "")
    if not token_iss.endswith(expected_realm):
        raise TokenValidationError(f"Invalid issuer: {token_iss}")

    return claims


class KeycloakAdminClient:
    """Client pour l'API Admin REST de Keycloak, authentifié via
    client_credentials avec le client confidentiel svc-auth-gateway."""

    def __init__(self) -> None:
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    async def _get_service_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expires_at - 10:
            return self._token

        url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.keycloak_client_id,
                    "client_secret": settings.keycloak_client_secret,
                },
            )
            resp.raise_for_status()
            payload = resp.json()

        self._token = payload["access_token"]
        self._token_expires_at = now + payload.get("expires_in", 60)
        return self._token

    async def create_user(
        self,
        *,
        username: str,
        email: str,
        temp_password: str,
        realm_role: str,
        establishment_ids: list[str],
        is_super_admin: bool = False,
    ) -> str:
        """Crée l'utilisateur dans Keycloak, assigne son rôle réaliste et ses
        claims multi-tenant (D2), retourne l'UUID Keycloak (`sub`)."""
        token = await self._get_service_token()
        headers = {"Authorization": f"Bearer {token}"}
        base = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            create_resp = await client.post(
                f"{base}/users",
                headers=headers,
                json={
                    "username": username,
                    "email": email,
                    "enabled": True,
                    "emailVerified": True,
                    "attributes": {
                        "establishment_ids": establishment_ids,
                        "is_super_admin": ["true" if is_super_admin else "false"],
                    },
                    "credentials": [
                        {"type": "password", "value": temp_password, "temporary": True}
                    ],
                    # Le lien du téléphone n'est plus une required action
                    # Keycloak native — le navigateur natif (hybrid/QR) s'est
                    # montré peu fiable selon l'appareil. Après
                    # UPDATE_PASSWORD, le frontend redirige lui-même vers
                    # /link-phone (relais QR maison) si users.webauthn_linked
                    # est encore false — voir app/api/auth/callback.
                    "requiredActions": ["UPDATE_PASSWORD"],
                },
            )
            if create_resp.status_code == 409:
                raise ValueError(f"User already exists in Keycloak: {username}")
            create_resp.raise_for_status()

            location = create_resp.headers["Location"]
            user_id = location.rstrip("/").split("/")[-1]

            role_resp = await client.get(f"{base}/roles/{realm_role}", headers=headers)
            role_resp.raise_for_status()
            role_repr = role_resp.json()

            assign_resp = await client.post(
                f"{base}/users/{user_id}/role-mappings/realm",
                headers=headers,
                json=[role_repr],
            )
            assign_resp.raise_for_status()

        return user_id

    async def get_required_actions(self, user_id: str) -> list[str]:
        """Retourne les requiredActions Keycloak encore en attente pour ce
        compte — si "UPDATE_PASSWORD" en fait toujours partie, l'utilisateur
        ne s'est jamais connecté avec son mot de passe temporaire."""
        token = await self._get_service_token()
        headers = {"Authorization": f"Bearer {token}"}
        base = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{base}/users/{user_id}", headers=headers)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            return resp.json().get("requiredActions", [])

    async def delete_user(self, user_id: str) -> None:
        """Suppression définitive côté Keycloak — idempotent (404 toléré, le
        compte a pu déjà être supprimé d'un appel précédent)."""
        token = await self._get_service_token()
        headers = {"Authorization": f"Bearer {token}"}
        base = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(f"{base}/users/{user_id}", headers=headers)
            if resp.status_code != 404:
                resp.raise_for_status()

    async def set_user_enabled(self, user_id: str, enabled: bool) -> None:
        """Active/désactive le compte dans Keycloak (login refusé si disabled) —
        utilisé pour la "suppression" (réversible) d'un utilisateur côté admin."""
        token = await self._get_service_token()
        headers = {"Authorization": f"Bearer {token}"}
        base = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.put(f"{base}/users/{user_id}", headers=headers, json={"enabled": enabled})
            resp.raise_for_status()

    async def list_events(self, *, max_results: int = 100) -> list[dict[str, Any]]:
        """Derniers events LOGIN/LOGIN_ERROR (auth_audit_log, biom.txt) —
        triés par Keycloak du plus récent au plus ancien. Nécessite
        eventsEnabled (scripts/keycloak_setup.py:configure_events). Pas de
        filtre dateFrom ici (granularité jour seulement côté Keycloak, trop
        grossière pour un polling fréquent) : le dédup se fait côté appelant
        via keycloak_event_id (voir audit_poller.py)."""
        token = await self._get_service_token()
        headers = {"Authorization": f"Bearer {token}"}
        base = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{base}/events",
                headers=headers,
                params={"type": ["LOGIN", "LOGIN_ERROR"], "max": max_results},
            )
            resp.raise_for_status()
            return resp.json()

    async def set_user_role(self, user_id: str, new_role: str) -> None:
        """Remplace le rôle métier réaliste de l'utilisateur par `new_role` —
        retire les rôles métier connus actuellement assignés puis ajoute le
        nouveau (un utilisateur ne porte qu'un seul rôle métier à la fois)."""
        token = await self._get_service_token()
        headers = {"Authorization": f"Bearer {token}"}
        base = f"{settings.keycloak_url}/admin/realms/{settings.keycloak_realm}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            current_resp = await client.get(f"{base}/users/{user_id}/role-mappings/realm", headers=headers)
            current_resp.raise_for_status()
            current_roles = current_resp.json()
            to_remove = [r for r in current_roles if r["name"] in APP_REALM_ROLES]
            if to_remove:
                del_resp = await client.request(
                    "DELETE", f"{base}/users/{user_id}/role-mappings/realm", headers=headers, json=to_remove
                )
                del_resp.raise_for_status()

            role_resp = await client.get(f"{base}/roles/{new_role}", headers=headers)
            role_resp.raise_for_status()
            role_repr = role_resp.json()

            assign_resp = await client.post(
                f"{base}/users/{user_id}/role-mappings/realm", headers=headers, json=[role_repr]
            )
            assign_resp.raise_for_status()


keycloak_admin = KeycloakAdminClient()
