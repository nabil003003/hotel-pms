class UserAlreadyExistsError(Exception):
    pass


class KeycloakAdminError(Exception):
    pass


class ElevationSessionInvalidError(Exception):
    """Token inconnu, expiré, ou déjà consommé — pas de distinction entre
    ces trois cas dans le message d'erreur exposé (évite de laisser un
    appelant sonder l'existence d'un token)."""

    pass


class UserNotFoundError(Exception):
    pass


class PhoneLinkSessionInvalidError(Exception):
    """Token inconnu, expiré, ou déjà complété."""

    pass


class LoginLinkSessionInvalidError(Exception):
    """Token inconnu, expiré, déjà complété, ou déjà réclamé."""

    pass
