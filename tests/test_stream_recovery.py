import pytest

from app.orchestration.stream import RedisRunStream


class RedisStub:
    async def xautoclaim(self, *_args, **_kwargs):
        return ["0-1", [["old-1", {"run_id": "run-1"}]], []]


@pytest.mark.asyncio
async def test_pending_messages_are_claimed() -> None:
    stream = RedisRunStream(RedisStub(), "runs")
    assert await stream.claim_pending("group", "consumer") == [("old-1", {"run_id": "run-1"})]

