from typing import Protocol

from app.adapters.base import AdapterResponse
from app.orchestration.terminal import should_stop, should_wait_for_reviewer


class SendActions(Protocol):
    async def accept(self, delivery_id: str, *, token: str, key: str) -> AdapterResponse: ...
    async def pickup(self, delivery_id: str, *, token: str, location: dict, recorded_at: str, key: str) -> AdapterResponse: ...
    async def deliver(self, delivery_id: str, *, token: str, location: dict, recorded_at: str, delivery_pin: str, key: str, photo_file_id: str | None = None, signature_file_id: str | None = None, note: str | None = None) -> AdapterResponse: ...


class SendCourierWorkflow:
    def __init__(self, adapter: SendActions) -> None:
        self.adapter = adapter

    async def advance(self, delivery_id: str, *, token: str, server_status: str, location: dict | None, recorded_at: str | None, delivery_pin: str | None, key_prefix: str) -> bool:
        if should_stop(server_status):
            return False
        if server_status == "OFFERED":
            await self.adapter.accept(delivery_id, token=token, key=f"{key_prefix}:accept")
        elif server_status == "ACCEPTED":
            if not location or not recorded_at:
                return False
            await self.adapter.pickup(delivery_id, token=token, location=location, recorded_at=recorded_at, key=f"{key_prefix}:pickup")
        elif server_status == "PICKED_UP":
            if not location or not recorded_at or should_wait_for_reviewer(server_status, required_value=delivery_pin):
                return False
            await self.adapter.deliver(delivery_id, token=token, location=location, recorded_at=recorded_at, delivery_pin=delivery_pin, key=f"{key_prefix}:deliver")
        return server_status in {"OFFERED", "ACCEPTED", "PICKED_UP"}
