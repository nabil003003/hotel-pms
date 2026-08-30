class RoomNotFoundError(Exception):
    pass


class InvalidTransitionError(Exception):
    def __init__(self, current: str, requested: str, allowed: list[str]):
        self.current = current
        self.requested = requested
        self.allowed = allowed
        super().__init__(f"Cannot transition from {current} to {requested}")


class ReasonRequiredError(Exception):
    pass
