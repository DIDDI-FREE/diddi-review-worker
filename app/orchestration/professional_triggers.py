"""Professional availability edge detection and one-shot request creation."""

from collections.abc import Awaitable, Callable
from typing import Any

from app.orchestration.reactive import AvailabilityTracker


class ProfessionalTriggerRunner:
    def __init__(self) -> None:
        self.availability = AvailabilityTracker()
        self._created: set[str] = set()

    async def on_availability(
        self,
        *,
        product: str,
        user_id: str,
        available: bool,
        create_request: Callable[[], Awaitable[Any]],
    ) -> Any | None:
        if not self.availability.transition_to_available(f"{product}:{user_id}", available):
            return None
        key = f"{product}:{user_id}"
        if key in self._created:
            return None
        result = await create_request()
        self._created.add(key)
        return result

    def rearm(self, *, product: str, user_id: str) -> None:
        self._created.discard(f"{product}:{user_id}")
