class MarketSegmentNotFoundError(Exception):
    pass


class CustomerNotFoundError(Exception):
    pass


class BookingNotFoundError(Exception):
    pass


class InvalidSegmentError(Exception):
    """`market_segment_id` inconnu, inactif, ou incohérent avec `source`
    (ex: segment PARTENAIRES sans `partner_id`)."""

    pass


class RoomUnavailableError(Exception):
    """Chevauchement de dates détecté sur `room_id`, ou verrou Redis déjà
    posé par une autre requête concurrente."""

    pass


class NoRoomAvailableError(Exception):
    """Aucune chambre de la catégorie demandée n'est libre sur la période
    (résolution room_category -> room_id, chemin OTA)."""

    pass


class InvalidStatusTransitionError(Exception):
    pass


class UpsellRequiresValidationError(Exception):
    """Room shift vers une catégorie différente sans token d'élévation
    valide — spec Workflow F, décision D8."""

    pass


class RoomConflictError(Exception):
    def __init__(self, message: str, conflicting_booking_id):
        super().__init__(message)
        self.conflicting_booking_id = conflicting_booking_id


class RoomShiftLockedError(Exception):
    pass


class ElevationInvalidError(Exception):
    pass


class BusinessDateLockedError(Exception):
    """Date métier verrouillée par night-audit-service (D12) — 423 LOCKED."""

    pass
