"""Read-only adapters that normalize currently exposed observation endpoints."""

from dataclasses import dataclass
from typing import Any, Protocol

from app.orchestration.reactive import ObservedTrigger, TriggerKind


class ReadClient(Protocol):
    async def get(self, path: str, *, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]: ...


@dataclass(frozen=True)
class PollContext:
    user_id: str
    token: str


def _items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    value = payload.get("items", payload.get("data", payload))
    return value if isinstance(value, list) else []


class GoPoller:
    def __init__(self, client: ReadClient) -> None:
        self.client = client

    async def rides(self, context: PollContext, *, role: str = "passenger") -> list[ObservedTrigger]:
        payload = await self.client.get("v1/rides", token=context.token, params={"role": role, "page": 1, "page_size": 100})
        return [ObservedTrigger(str(r.get("id")), TriggerKind.CONSUMER_RESOURCE_CREATED, "diddigo", role, context.user_id, str(r["id"]), str(r.get("updated_at", r.get("status")))) for r in _items(payload) if r.get("id")]


class SendPoller:
    def __init__(self, client: ReadClient) -> None:
        self.client = client

    async def offers(self, context: PollContext) -> list[ObservedTrigger]:
        payload = await self.client.get("v1/courier/offers", token=context.token)
        events = []
        for offer in _items(payload):
            resource_id = offer.get("delivery_id") or offer.get("id")
            if resource_id:
                events.append(ObservedTrigger(str(resource_id), TriggerKind.CONSUMER_RESOURCE_CREATED, "diddisend", "courier", context.user_id, str(resource_id), str(offer.get("updated_at", offer.get("status")))))
        return events

    async def sender_deliveries(self, context: PollContext) -> list[ObservedTrigger]:
        payload = await self.client.get("v1/deliveries", token=context.token, params={"role": "sender", "limit": 100})
        return [ObservedTrigger(str(d.get("id")), TriggerKind.CONSUMER_RESOURCE_CREATED, "diddisend", "sender", context.user_id, str(d["id"]), str(d.get("updated_at", d.get("status")))) for d in _items(payload) if d.get("id")]


class FoodPoller:
    def __init__(self, client: ReadClient) -> None:
        self.client = client

    async def restaurant_orders(self, context: PollContext, restaurant_id: str) -> list[ObservedTrigger]:
        payload = await self.client.get(f"food/v1/restaurants/{restaurant_id}/orders", token=context.token)
        return [ObservedTrigger(str(o["id"]), TriggerKind.CONSUMER_RESOURCE_CREATED, "diddifood", "restaurant", context.user_id, str(o["id"]), str(o.get("updated_at", o.get("status")))) for o in _items(payload) if o.get("id")]
