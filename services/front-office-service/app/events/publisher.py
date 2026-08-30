"""Événements publiés — `booking.checked_in`/`booking.checked_out` sur
`amh.booking` (front-office-service, pas reservation-service, cf. Appendix
C) ; `folio.charge_added`/`folio.payment_added` sur `amh.folio` (déclaré
Sprint 1, `payment_added` jamais publié jusqu'ici — analytics-service n'avait
donc aucun moyen de refléter un encaissement)."""

from __future__ import annotations

from app.infrastructure.rabbitmq import publish


async def publish_booking_checked_in(
    booking_id: str, room_id: str, folio_ids: list[str], establishment_id: str, business_date: str,
    *, guest_name: str, room_number: str,
) -> None:
    await publish(
        "amh.booking", "booking.checked_in",
        {
            "booking_id": booking_id, "room_id": room_id, "folio_ids": folio_ids,
            "establishment_id": establishment_id, "business_date": business_date,
            # guest_name/room_number : uniquement pour un texte de notification
            # lisible côté notification-service (D11 bis) — booking_id/room_id
            # restent la référence technique pour les autres consumers.
            "guest_name": guest_name, "room_number": room_number,
        },
    )


async def publish_booking_checked_out(
    booking_id: str, room_id: str, final_balance: float, establishment_id: str,
    *, guest_name: str, room_number: str,
) -> None:
    await publish(
        "amh.booking", "booking.checked_out",
        {
            "booking_id": booking_id, "room_id": room_id, "final_balance": final_balance,
            "establishment_id": establishment_id, "guest_name": guest_name, "room_number": room_number,
        },
    )


async def publish_folio_charge_added(
    folio_id: str, booking_id: str, amount: float, poste: str, establishment_id: str, business_date: str
) -> None:
    """`booking_id` ajouté au payload (au-delà du strict `{folio_id, amount,
    poste, establishment_id}` de l'Appendix C) : analytics-service en a
    besoin pour résoudre le `market_segment_id` via reservation-service et
    ventiler le CA par segment, sans lui faire refaire un aller-retour
    supplémentaire via front-office-service. `business_date` ajouté de même :
    la date métier du folio, pas `date.today()` côté analytics-service (même
    incident que le check-in — cf. night_audit_client)."""
    await publish(
        "amh.folio", "folio.charge_added",
        {
            "folio_id": folio_id, "booking_id": booking_id, "amount": amount, "poste": poste,
            "establishment_id": establishment_id, "business_date": business_date,
        },
    )


async def publish_payment_added(
    payment_id: str, folio_id: str, booking_id: str, mode: str, montant: float,
    establishment_id: str, business_date: str,
) -> None:
    """Jusqu'ici jamais publié : un encaissement restait une écriture locale
    à `fo_db`, invisible d'analytics-service (aucun consumer/colonne pour ça
    — cf. `handle_payment_added`)."""
    await publish(
        "amh.folio", "folio.payment_added",
        {
            "payment_id": payment_id, "folio_id": folio_id, "booking_id": booking_id, "mode": mode,
            "montant": montant, "establishment_id": establishment_id, "business_date": business_date,
        },
    )
