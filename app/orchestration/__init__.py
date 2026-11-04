from uuid import uuid4

from app.orchestration.stream import RedisRunStream
from app.persistence import InMemoryRunRepository, RunRecord
from app.scenarios import RunRequest


class Orchestrator:
    def __init__(self, repository: InMemoryRunRepository, stream: RedisRunStream | None = None) -> None:
        self.repository, self.stream = repository, stream

    async def create(self, request: RunRequest) -> RunRecord:
        request.validate_contract()
        record = RunRecord(
            run_id=str(uuid4()), scenario=request.scenario.value,
            steps=[step.model_dump() | {"status": "queued"} for step in request.steps],
        )
        self.repository.save(record)
        if self.stream is not None:
            await self.stream.publish(record.run_id)
        return record

    def retry(self, run_id: str) -> RunRecord:
        return self.repository.retry(run_id)

    def cancel(self, run_id: str) -> RunRecord:
        record = self.repository.get(run_id)
        if record is None:
            raise KeyError(run_id)
        if record.status in {"succeeded", "failed"}:
            raise ValueError("terminal run cannot be cancelled")
        record.status = "cancelled"
        return self.repository.save(record)
