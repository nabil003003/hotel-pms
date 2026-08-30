"""Vérification JWT (JWKS Keycloak) — identique à establishment-service par
choix (isolation microservices, pas de lib partagée, cf. D2)."""

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
    jwks = await _get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise TokenValidationError("Malformed token header") from exc

    key = next((k for k in jwks.get("keys", []) if k.get("kid") == unverified_header.get("kid")), None)
    if key is None:
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
