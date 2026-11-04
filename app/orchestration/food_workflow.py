from typing import Protocol

from app.adapters.base import AdapterResponse
from app.orchestration.terminal import should_stop


class FoodActions(Protocol):
    async def accept_order(self, restaurant_id: str, order_id: str, *, token: str, prep_minutes: int, key: str) -> AdapterResponse: ...
    async def mark_ready(self, restaurant_id: str, order_id: str, *, token: str, key: str) -> AdapterResponse: ...


class FoodRestaurantWorkflow:
    def __init__(self, adapter: FoodActions) -> None:
        self.adapter = adapter

    async def advance(self, restaurant_id: str, order_id: str, *, token: str, server_status: str, prep_minutes: int | None, key_prefix: str) -> bool:
        if should_stop(server_status):
            return False
        if server_status == "PENDING":
            if prep_minutes is None:
                return False
            await self.adapter.accept_order(restaurant_id, order_id, token=token, prep_minutes=prep_minutes, key=f"{key_prefix}:accept")
        elif server_status == "PREPARING":
            await self.adapter.mark_ready(restaurant_id, order_id, token=token, key=f"{key_prefix}:ready")
        return server_status in {"PENDING", "PREPARING"}
