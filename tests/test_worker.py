from unittest.mock import AsyncMock

import pytest

from app.adapters.diddifood import DiddiFoodAdapter
from app.adapters.diddigo import DiddiGoAdapter
from app.adapters.diddisend import DiddiSendAdapter
from app.orchestration.executor import StepExecutor
from app.orchestration.worker import ReviewRunWorker
from app.persistence import InMemoryRunRepository, RunRecord


class FakeStream:
    def __init__(self) -> None:
        self.acked: list[str] = []

    async def ensure_group(self, group: str) -> None:
        self.group = group

    async def read(self, group: str, consumer: str) -> list[tuple[str, dict[str, str]]]:
        return [("1-0", {"run_id": "run-1"})]

    async def claim_pending(self, group: str, consumer: str) -> list[tuple[str, dict[str, str]]]:
        return []

    async def ack(self, group: str, entry_id: str) -> int:
        self.acked.append(entry_id)
        return 1


@pytest.mark.asyncio
async def test_worker_acks_after_processing() -> None:
    repo = InMemoryRunRepository()
    repo.save(RunRecord("run-1", "diddigo-reviews", steps=[{"key": "s", "product": "diddigo", "role": "passenger", "resource_id": "ride", "rating": 5}]))
    go = DiddiGoAdapter("go", "http://go", None)
    go.rate_ride = AsyncMock(return_value=type("Response", (), {"status": 201, "payload": {}})())
    worker = ReviewRunWorker(
        stream=FakeStream(), repository=repo,
        executor=StepExecutor(go=go, send=DiddiSendAdapter("send", "http://send", None), food=DiddiFoodAdapter("food", "http://food", None)),
        token_resolver=AsyncMock(return_value="short-lived-jwt"),
    )
    await worker.start()
    assert await worker.process_once() == 1
    assert repo.get("run-1").status == "succeeded"
    assert worker.stream.acked == ["1-0"]
