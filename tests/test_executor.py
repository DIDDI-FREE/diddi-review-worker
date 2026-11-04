from unittest.mock import AsyncMock

import pytest

from app.adapters.base import AdapterError, AdapterResponse
from app.adapters.diddifood import DiddiFoodAdapter
from app.adapters.diddigo import DiddiGoAdapter
from app.adapters.diddisend import DiddiSendAdapter
from app.orchestration.executor import StepExecutor, execute_run
from app.persistence import RunRecord


def executor() -> StepExecutor:
    return StepExecutor(
        go=DiddiGoAdapter("go", "http://go", None),
        send=DiddiSendAdapter("send", "http://send", None),
        food=DiddiFoodAdapter("food", "http://food", None),
    )


@pytest.mark.asyncio
async def test_executor_dispatches_sender_route() -> None:
    runner = executor()
    runner.send.rate_sender = AsyncMock(return_value=AdapterResponse(201, {"id": "rating-1"}))
    result = await runner.execute({"product": "diddisend", "role": "sender", "resource_id": "d-1", "rating": 5, "key": "k"}, token="jwt")
    assert result.status == "succeeded"
    runner.send.rate_sender.assert_awaited_once()


@pytest.mark.asyncio
async def test_business_refusal_is_not_retryable() -> None:
    runner = executor()
    runner.go.rate_ride = AsyncMock(side_effect=AdapterError("diddigo", 409, "RATING_ALREADY_SUBMITTED"))
    result = await runner.execute({"product": "diddigo", "role": "passenger", "resource_id": "r-1", "rating": 5, "key": "k"}, token="jwt")
    assert result.status == "failed"
    assert result.retryable is False


@pytest.mark.asyncio
async def test_run_stops_at_first_failed_step() -> None:
    runner = executor()
    runner.send.rate_sender = AsyncMock(side_effect=ConnectionError())
    run = RunRecord("run-1", "diddisend-reviews", steps=[
        {"key": "first", "product": "diddisend", "role": "sender", "resource_id": "d-1", "rating": 5},
        {"key": "second", "product": "diddisend", "role": "courier", "resource_id": "d-1", "rating": 5},
    ])
    await execute_run(run, executor=runner, token="jwt")
    assert run.status == "failed"
    assert run.steps[0]["error_code"] == "UPSTREAM_UNAVAILABLE"
    assert run.steps[1]["status"] == "queued"

