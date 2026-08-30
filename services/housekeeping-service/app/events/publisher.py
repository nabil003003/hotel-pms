from app.infrastructure.rabbitmq import publish_room_event


async def publish_status_changed(payload: dict) -> None:
    await publish_room_event("room.status_changed", payload)


async def publish_incident_reported(payload: dict) -> None:
    await publish_room_event("room.incident_reported", payload)
