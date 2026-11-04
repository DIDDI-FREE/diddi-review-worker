"""Pure decision layer for the reactive review assistant.

This module deliberately does not call business APIs. Adapters may only be
invoked after a trusted, explicit event has been observed by a product-specific
detector.
"""

from dataclasses import dataclass
from enum import StrEnum


class TriggerKind(StrEnum):
    CONSUMER_RESOURCE_CREATED = "consumer_resource_created"
    PROFESSIONAL_AVAILABLE = "professional_available"


@dataclass(frozen=True)
class AccountBinding:
    reviewer_user_id: str
    tested_role: str
    counter_role: str
    counter_user_id: str
    product: str


@dataclass(frozen=True)
class ObservedTrigger:
    event_id: str
    kind: TriggerKind
    product: str
    role: str
    user_id: str
    resource_id: str | None = None
    state_version: str | None = None


@dataclass(frozen=True)
class Reaction:
    action: str
    binding: AccountBinding
    resource_id: str | None


class ReactiveCoordinator:
    """Maps trusted product events to at-most-once counter-role reactions."""

    def __init__(self, bindings: list[AccountBinding]) -> None:
        self._bindings = {(b.product, b.tested_role, b.reviewer_user_id): b for b in bindings}
        self._handled: set[str] = set()
        self._terminal: set[str] = set()

    def react(self, trigger: ObservedTrigger) -> Reaction | None:
        key = self._key(trigger)
        if key in self._handled or key in self._terminal:
            return None
        binding = self._bindings.get((trigger.product, trigger.role, trigger.user_id))
        if binding is None:
            return None
        if trigger.kind is TriggerKind.PROFESSIONAL_AVAILABLE and not trigger.resource_id:
            return None
        self._handled.add(key)
        return Reaction("play_counter_role", binding, trigger.resource_id)

    def mark_terminal(self, trigger: ObservedTrigger) -> None:
        self._terminal.add(self._key(trigger))

    def rearm(self, trigger: ObservedTrigger) -> None:
        self._handled.discard(self._key(trigger))

    @staticmethod
    def _key(trigger: ObservedTrigger) -> str:
        version = trigger.state_version or trigger.resource_id or trigger.event_id
        return f"{trigger.product}:{trigger.role}:{trigger.user_id}:{version}"
