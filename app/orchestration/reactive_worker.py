"""Polling loop glue; business actions are injected, never hard-coded here."""

import asyncio
from collections.abc import Awaitable, Callable
from inspect import isawaitable
from typing import Any

from app.orchestration.reactive import ObservedTrigger, ReactiveCoordinator
from app.persistence.event_ledger import InMemoryEventLedger

ReactionHandler = Callable[[ObservedTrigger], Awaitable[None]]
Poller = Callable[[], Awaitable[list[ObservedTrigger]]]


class ReactivePollingWorker:
    def __init__(
        self,
        *,
        coordinator: ReactiveCoordinator,
        ledger: InMemoryEventLedger | Any,
        reaction_handler: ReactionHandler | None = None,
    ) -> None:
        self.coordinator = coordinator
        self.ledger = ledger
        self.reaction_handler = reaction_handler

    async def process(self, events: list[ObservedTrigger]) -> int:
        processed = 0
        for event in events:
            key = self.coordinator.event_key(event)
            claim = self.ledger.claim(key)
            if isawaitable(claim):
                claim = await claim
            if not claim:
                continue
            reaction = self.coordinator.react(event)
            if reaction is None:
                continue
            if self.reaction_handler is None:
                # No confirmed action contract: leave the event observed but idle.
                continue
            await self.reaction_handler(event)
            processed += 1
        return processed

    async def poll_once(self, poller: Poller) -> int:
        """Poll one explicitly configured source; no source means no action."""
        return await self.process(await poller())

    async def process_pollers(self, pollers: list[Poller]) -> int:
        """Run the configured read-only pollers once and process their events."""
        if not pollers:
            return 0
        batches = await asyncio.gather(*(poller() for poller in pollers))
        return await self.process([event for batch in batches for event in batch])
