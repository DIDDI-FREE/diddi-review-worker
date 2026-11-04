from dataclasses import dataclass
from typing import Any

from app.adapters.base import AdapterError, AdapterResponse
from app.adapters.diddifood import DiddiFoodAdapter
from app.adapters.diddigo import DiddiGoAdapter
from app.adapters.diddisend import DiddiSendAdapter
from app.persistence import RunRecord


@dataclass(frozen=True)
class StepExecutionResult:
    status: str
    response: AdapterResponse | None = None
    error_code: str | None = None
    retryable: bool = False


class StepExecutor:
    def __init__(self, *, go: DiddiGoAdapter, send: DiddiSendAdapter, food: DiddiFoodAdapter) -> None:
        self.go, self.send, self.food = go, send, food

    async def execute(self, step: dict[str, Any], *, token: str) -> StepExecutionResult:
        product, role = step["product"], step["role"]
        args = {"token": token, "rating": step["rating"], "comment": step.get("comment"), "key": step["key"]}
        try:
            if product == "diddigo":
                response = await self.go.rate_ride(step["resource_id"], **args)
            elif product == "diddisend" and role == "sender":
                response = await self.send.rate_sender(step["resource_id"], **args)
            elif product == "diddisend" and role == "courier":
                response = await self.send.rate_courier(step["resource_id"], **args)
            elif product == "diddifood" and role == "customer":
                response = await self.food.rate_customer(step["resource_id"], **args)
            else:
                return StepExecutionResult("failed", error_code="UNSUPPORTED_REVIEW_ROLE")
        except AdapterError as exc:
            return StepExecutionResult("failed", error_code=exc.code, retryable=exc.retryable)
        except (TimeoutError, ConnectionError):
            return StepExecutionResult("failed", error_code="UPSTREAM_UNAVAILABLE", retryable=True)
        return StepExecutionResult("succeeded", response=response)


async def execute_run(run: RunRecord, *, executor: StepExecutor, token: str) -> RunRecord:
    if run.status in {"cancelled", "succeeded"}:
        return run
    run.status = "running"
    for step in run.steps:
        step.setdefault("status", "queued")
    for step in run.steps:
        if step.get("status") == "succeeded":
            continue
        result = await executor.execute(step, token=token)
        step["status"] = result.status
        if result.error_code:
            step["error_code"] = result.error_code
            step["retryable"] = result.retryable
        if result.status == "failed":
            run.status = "failed"
            return run
    run.status = "succeeded"
    return run
