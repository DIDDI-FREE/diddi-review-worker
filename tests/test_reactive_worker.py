import pytest

from app.orchestration.reactive import (
    AccountBinding,
    ObservedTrigger,
    ReactiveCoordinator,
    TriggerKind,
)
from app.orchestration.reactive_worker import ReactivePollingWorker
from app.persistence.event_ledger import InMemoryEventLedger


def trigger():
    return ObservedTrigger("event-1", TriggerKind.CONSUMER_RESOURCE_CREATED, "diddigo", "passenger", "reviewer", "ride-1", "v1")


@pytest.mark.asyncio
async def test_worker_waits_without_confirmed_action_handler():
    worker = ReactivePollingWorker(
        coordinator=ReactiveCoordinator([AccountBinding("reviewer", "passenger", "driver", "driver", "diddigo")]),
        ledger=InMemoryEventLedger(),
    )
    assert await worker.process([trigger(), trigger()]) == 0


@pytest.mark.asyncio
async def test_worker_invokes_handler_once_for_new_event():
    seen = []

    async def handle(event):
        seen.append(event.resource_id)

    worker = ReactivePollingWorker(
        coordinator=ReactiveCoordinator([AccountBinding("reviewer", "passenger", "driver", "driver", "diddigo")]),
        ledger=InMemoryEventLedger(),
        reaction_handler=handle,
    )
    assert await worker.process([trigger(), trigger()]) == 1
    assert seen == ["ride-1"]
