class ConnectionNotFoundError(Exception):
    pass


class OtaMappingNotFoundError(Exception):
    """Aucun `ota_mappings` (establishment-service) ne correspond au
    room_type_id envoyé par l'OTA — spec Workflow C, réponse 422
    `MAPPING_ERROR`."""

    pass


class OtaConflictError(Exception):
    """Une `ota_reference` déjà traitée revient dans un nouveau webhook —
    spec Workflow C, réponse 409 `OTA_CONFLICT`."""

    pass


class InvalidWebhookSignatureError(Exception):
    pass
