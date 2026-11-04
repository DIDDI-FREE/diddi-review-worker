import json
from typing import Any


class RedisRunStream:
    """Small Redis Streams boundary; business orchestration remains outside Redis."""

    def __init__(self, redis: Any, stream_name: str) -> None:
        self.redis = redis
        self.stream_name = stream_name

    async def publish(self, run_id: str) -> str:
        return await self.redis.xadd(self.stream_name, {"run_id": run_id})

    async def ensure_group(self, group: str) -> None:
        try:
            await self.redis.xgroup_create(self.stream_name, group, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def read(self, group: str, consumer: str, count: int = 10) -> list[tuple[str, dict[str, str]]]:
        entries = await self.redis.xreadgroup(group, consumer, {self.stream_name: ">"}, count=count, block=1000)
        return [(entry_id, fields) for _stream, items in entries for entry_id, fields in items]

    async def ack(self, group: str, entry_id: str) -> int:
        return await self.redis.xack(self.stream_name, group, entry_id)

    async def claim_pending(self, group: str, consumer: str, min_idle_ms: int = 30_000) -> list[tuple[str, dict[str, str]]]:
        result = await self.redis.xautoclaim(self.stream_name, group, consumer, min_idle_ms, "0-0", count=10)
        entries = result[1] if len(result) > 1 else []
        return [(entry_id, fields) for entry_id, fields in entries]

    @staticmethod
    def encode_event(event: dict[str, Any]) -> str:
        return json.dumps(event, separators=(",", ":"), sort_keys=True)
