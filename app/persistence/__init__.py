from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class RunRecord:
    run_id: str
    scenario: str
    status: str = "queued"
    steps: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InMemoryRunRepository:
    def __init__(self) -> None:
        self._runs: dict[str, RunRecord] = {}

    def save(self, run: RunRecord) -> RunRecord:
        self._runs[run.run_id] = run
        return run

    def get(self, run_id: str) -> RunRecord | None:
        return self._runs.get(run_id)

    def retry(self, run_id: str) -> RunRecord:
        record = self._runs.get(run_id)
        if record is None:
            raise KeyError(run_id)
        if record.status not in {"failed", "cancelled"}:
            raise ValueError("only failed or cancelled runs can be retried")
        record.status = "queued"
        for step in record.steps:
            if step.get("status") == "failed":
                step["status"] = "queued"
        return self.save(record)
