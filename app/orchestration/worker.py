from collections.abc import Awaitable, Callable

from app.orchestration.executor import StepExecutor, execute_run
from app.orchestration.stream import RedisRunStream
from app.persistence import InMemoryRunRepository

TokenResolver = Callable[[str], Awaitable[str]]


class ReviewRunWorker:
    def __init__(
        self,
        *,
        stream: RedisRunStream,
        repository: InMemoryRunRepository,
        executor: StepExecutor,
        token_resolver: TokenResolver,
        group: str = "review-runner",
        consumer: str = "runner-1",
    ) -> None:
        self.stream, self.repository, self.executor = stream, repository, executor
        self.token_resolver, self.group, self.consumer = token_resolver, group, consumer

    async def start(self) -> None:
        await self.stream.ensure_group(self.group)

    async def process_once(self) -> int:
        processed = 0
        pending = await self.stream.claim_pending(self.group, self.consumer)
        fresh = await self.stream.read(self.group, self.consumer)
        for entry_id, fields in pending + fresh:
            run_id = fields.get("run_id")
            run = self.repository.get(run_id) if run_id else None
            if run is not None and run.status not in {"succeeded", "cancelled"}:
                token = await self.token_resolver(run_id)
                await execute_run(run, executor=self.executor, token=token)
                self.repository.save(run)
            await self.stream.ack(self.group, entry_id)
            processed += 1
        return processed
