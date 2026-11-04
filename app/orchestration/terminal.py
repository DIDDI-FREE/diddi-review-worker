"""Terminal-state and reviewer-wait guards shared by product workflows."""


TERMINAL_STATUSES = frozenset({"CANCELLED", "CANCELED", "DECLINED", "REJECTED", "COMPLETED", "DELIVERED", "CLOSED"})


def should_stop(status: str) -> bool:
    return status.upper() in TERMINAL_STATUSES


def should_wait_for_reviewer(status: str, *, required_value: object | None) -> bool:
    return status.upper() in {"ARRIVED", "PICKED_UP", "PREPARING"} and required_value is None
