import pytest

from app.orchestration.reactive import AccountBinding, ObservedTrigger, ReactiveCoordinator, TriggerKind
from app.orchestration.reactive_worker import ReactivePollingWorker
from app.persistence.event_ledger import InMemoryEventLedger


@pytest.mark.asyncio
async def test_worker_processes_only_events_from_configured_pollers():
    seen = []

    async def poller():
        return [ObservedTrigger("e1", TriggerKind.CONSUMER_RESOURCE_CREATED, "diddigo", "passenger", "u1", "r1", "v1")]

    async def handler(event):
        seen.append(event.resource_id)

    worker = ReactivePollingWorker(
        coordinator=ReactiveCoordinator([AccountBinding("u1", "passenger", "driver", "u2", "diddigo")]),
        ledger=InMemoryEventLedger(),
        reaction_handler=handler,
    )
    assert await worker.process_pollers([poller]) == 1
    assert seen == ["r1"]
    assert await worker.process_pollers([]) == 0
