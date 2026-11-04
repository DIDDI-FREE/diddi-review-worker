import pytest

from app.orchestration.reactive import (
    AccountBinding,
    ObservedTrigger,
    ReactiveCoordinator,
    TriggerKind,
)
from app.orchestration.reactive_worker import ReactivePollingWorker


class AsyncLedger:
    def __init__(self):
        self.keys = set()

    async def claim(self, key):
        if key in self.keys:
            return False
        self.keys.add(key)
        return True


@pytest.mark.asyncio
async def test_worker_accepts_async_sql_style_ledger_and_poller():
    seen = []

    async def poll():
        return [ObservedTrigger("e1", TriggerKind.CONSUMER_RESOURCE_CREATED, "diddigo", "passenger", "u1", "r1", "v1")]

    async def handle(event):
        seen.append(event.resource_id)

    worker = ReactivePollingWorker(
        coordinator=ReactiveCoordinator([AccountBinding("u1", "passenger", "driver", "u2", "diddigo")]),
        ledger=AsyncLedger(),
        reaction_handler=handle,
    )
    assert await worker.poll_once(poll) == 1
    assert seen == ["r1"]
