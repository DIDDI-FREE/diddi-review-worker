from typing import Protocol

from app.adapters.base import AdapterResponse
from app.orchestration.terminal import should_stop, should_wait_for_reviewer


class GoActions(Protocol):
    async def accept_ride(self, ride_id: str, *, token: str, key: str) -> AdapterResponse: ...
    async def arrive(self, ride_id: str, *, token: str, key: str) -> AdapterResponse: ...
    async def start(self, ride_id: str, *, token: str, code: str, key: str) -> AdapterResponse: ...
    async def update_status(self, ride_id: str, *, token: str, status: str, key: str) -> AdapterResponse: ...


class GoDriverWorkflow:
    def __init__(self, adapter: GoActions) -> None:
        self.adapter = adapter

    async def advance(self, ride_id: str, *, token: str, server_status: str, start_code: str | None, key_prefix: str) -> bool:
        if should_stop(server_status):
            return False
        if server_status == "REQUESTED":
            await self.adapter.accept_ride(ride_id, token=token, key=f"{key_prefix}:accept")
        elif server_status == "ACCEPTED":
            await self.adapter.arrive(ride_id, token=token, key=f"{key_prefix}:arrive")
        elif server_status == "ARRIVED":
            if should_wait_for_reviewer(server_status, required_value=start_code):
                return False
            await self.adapter.start(ride_id, token=token, code=start_code, key=f"{key_prefix}:start")
        elif server_status == "IN_PROGRESS":
            await self.adapter.update_status(ride_id, token=token, status="COMPLETED", key=f"{key_prefix}:complete")
        return server_status in {"REQUESTED", "ACCEPTED", "ARRIVED", "IN_PROGRESS"}
