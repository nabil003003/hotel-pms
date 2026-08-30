"""Client REST vers pricing-service. Toute erreur (réseau ou réponse non-2xx)
est avalée et retourne `None` plutôt que de propager : la règle de
résilience du spec (ligne 1353) veut qu'une réservation puisse être créée
sans tarif calculé si pricing-service est indisponible OU si aucun tarif
n'est configuré pour la période demandée — les deux cas ont le même
traitement côté reservation-service."""

from __future__ import annotations

import logging
import time
from datetime import date as date_type
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}

# Perf (Sprint 8, D15) : voir la même note dans establishment_client.py —
# client HTTP partagé plutôt qu'un `async with httpx.AsyncClient(...)` par
# appel, pour bénéficier du keep-alive sous concurrence.
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=5.0)
    return _client


async def _get_service_token() -> str:
    now = time.time()
    if _token_cache["access_token"] is not None and now < _token_cache["expires_at"] - 10:
        return _token_cache["access_token"]

    url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
    resp = await _get_client().post(
        url,
        data={
            "grant_type": "client_credentials",
            "client_id": settings.keycloak_client_id,
            "client_secret": settings.keycloak_client_secret,
        },
    )
    resp.raise_for_status()
    body = resp.json()

    _token_cache["access_token"] = body["access_token"]
    _token_cache["expires_at"] = now + body.get("expires_in", 60)
    return _token_cache["access_token"]


async def _resolve_season_id(establishment_id: str, on_date: date_type) -> str | None:
    try:
        token = await _get_service_token()
        resp = await _get_client().get(
            f"{settings.pricing_service_url}/api/v1/pricing/{establishment_id}/seasons",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        seasons = resp.json()
    except httpx.HTTPError as exc:
        logger.warning("pricing-service unreachable while resolving season: %s", exc)
        return None

    for season in seasons:
        date_debut = date_type.fromisoformat(season["date_debut"])
        date_fin = date_type.fromisoformat(season["date_fin"])
        if date_debut <= on_date < date_fin:
            return season["id"]
    return None


async def calculate_public_rate(
    establishment_id: str, *, room_category: str, regime: str, date_from: date_type, date_to: date_type
) -> dict | None:
    try:
        token = await _get_service_token()
        resp = await _get_client().get(
            f"{settings.pricing_service_url}/api/v1/rates/calculate",
            params={
                "establishment_id": establishment_id,
                "room_category": room_category,
                "regime": regime,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        logger.warning("pricing-service rate calculation failed, proceeding without rate: %s", exc)
        return None


async def calculate_partner_rate(
    establishment_id: str, *, partner_id: str, room_category: str, on_date: date_type
) -> dict | None:
    season_id = await _resolve_season_id(establishment_id, on_date)
    if season_id is None:
        return None
    try:
        token = await _get_service_token()
        resp = await _get_client().get(
            f"{settings.pricing_service_url}/api/v1/rates/partner",
            params={
                "establishment_id": establishment_id,
                "partner_id": partner_id,
                "room_category": room_category,
                "season_id": season_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        logger.warning("pricing-service partner rate lookup failed, proceeding without rate: %s", exc)
        return None
