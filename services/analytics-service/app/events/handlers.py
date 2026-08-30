import logging

from app.domain.services import (
    handle_audit_closed,
    handle_booking_checked_in,
    handle_channel_booking_received,
    handle_folio_charge_added,
    handle_payment_added,
)
from app.infrastructure import redis_client as cache
from app.infrastructure.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def on_booking_event(routing_key: str, payload: dict) -> None:
    if routing_key == "booking.checked_out":
        # Pas d'écriture ici (nuitees/ca_brut ne bougent pas au check-out),
        # mais `get_kpi_today` calcule l'occupation en direct (nombre de
        # chambres actuellement status_checked_in) — la réponse mise en cache
        # doit donc être invalidée aussi au départ d'un client, pas seulement
        # à son arrivée, sous peine d'afficher une occupation figée jusqu'à
        # expiration du TTL.
        await cache.cache_delete(f"kpi:today:{payload['establishment_id']}")
        return
    if routing_key != "booking.checked_in":
        return  # seul checked_in alimente les compteurs Sprint 4 (D10)
    async with AsyncSessionLocal() as db:
        await handle_booking_checked_in(db, payload)


async def on_folio_event(routing_key: str, payload: dict) -> None:
    async with AsyncSessionLocal() as db:
        if routing_key == "folio.charge_added":
            await handle_folio_charge_added(db, payload)
        elif routing_key == "folio.payment_added":
            await handle_payment_added(db, payload)


async def on_channel_event(routing_key: str, payload: dict) -> None:
    if routing_key != "channel.booking_received":
        return  # channel.sync_failed : pas de table dédiée en Sprint 4, journalisé seulement
    async with AsyncSessionLocal() as db:
        await handle_channel_booking_received(db, payload)


async def on_audit_event(routing_key: str, payload: dict) -> None:
    async with AsyncSessionLocal() as db:
        await handle_audit_closed(db, payload)
