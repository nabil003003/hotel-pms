class SeasonNotFoundError(Exception):
    pass


class RateGridNotFoundError(Exception):
    pass


class RateGridAlreadyExistsError(Exception):
    pass


class TaxConfigNotFoundError(Exception):
    pass


class ExtrasCatalogItemNotFoundError(Exception):
    pass


class PartnerRateNotFoundError(Exception):
    pass


class PartnerRateAlreadyExistsError(Exception):
    pass


class PackageNotFoundError(Exception):
    pass


class RateNotAvailableError(Exception):
    """Aucune season/rate_grid ne couvre au moins une nuit du séjour demandé.
    reservation-service doit dégrader en `status_option` sans tarif plutôt
    que bloquer la réservation (règle de résilience du spec, ligne 1353)."""

    pass
