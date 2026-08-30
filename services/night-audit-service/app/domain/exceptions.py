class DiscrepancyError(Exception):
    """Écart débits/crédits détecté à la vérification pré-audit (spec ligne
    610-611) — bloque totalement le lancement du Night Audit."""

    def __init__(self, message: str, discrepancy: float):
        super().__init__(message)
        self.discrepancy = discrepancy


class AuditTokenInvalidError(Exception):
    """`X-Audit-Token` absent, expiré, déjà consommé, ou ne correspondant
    pas à l'établissement demandé."""

    pass


class NoActiveAuditError(Exception):
    """`POST /close` appelé sans vérification préalable réussie pour cette
    date/établissement."""

    pass


class AuditAlreadyClosedError(Exception):
    pass
