class FolioNotFoundError(Exception):
    pass


class RoomNotReadyError(Exception):
    """Précondition check-in : chambre pas `Propre`/`Contrôlée` (Workflow D,
    spec ligne 361) → 409 PRECONDITION_FAILED."""

    pass


class InvalidBookingStateError(Exception):
    """La réservation n'est pas dans un état permettant le check-in/check-out
    (ex: déjà checked_in, annulée...)."""

    pass


class FolioNotOpenError(Exception):
    pass


class FolioNotBalancedError(Exception):
    """Folio A non soldé au check-out (spec ligne 511 : la somme des
    paiements doit égaler exactement le solde)."""

    def __init__(self, message: str, balance):
        super().__init__(message)
        self.balance = balance


class OptimisticLockError(Exception):
    """`Folio.version` a changé entre lecture et écriture — concurrence
    détectée (spec §6.2, ligne 1335)."""

    pass


class CatalogItemNotFoundError(Exception):
    pass


class ReopenForbiddenError(Exception):
    """`POST /folios/{id}/reopen` — toujours 403, aucun contournement de
    rôle (spec, aucune exception documentée)."""

    pass


class BusinessDateLockedError(Exception):
    pass
