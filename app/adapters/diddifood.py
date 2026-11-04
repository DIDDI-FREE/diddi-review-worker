from app.adapters.base import AdapterResponse, HttpAdapter


class DiddiFoodAdapter(HttpAdapter):
    async def accept_order(self, restaurant_id: str, order_id: str, *, token: str, key: str, payload: dict | None = None) -> AdapterResponse:
        return await self.post(f"food/v1/restaurants/{restaurant_id}/orders/{order_id}/accept", token=token, payload=payload or {}, idempotency_key=key)

    async def mark_ready(self, restaurant_id: str, order_id: str, *, token: str, key: str) -> AdapterResponse:
        return await self.post(f"food/v1/restaurants/{restaurant_id}/orders/{order_id}/ready", token=token, payload={}, idempotency_key=key)

    async def rate_customer(self, order_id: str, *, token: str, rating: int, comment: str | None, key: str) -> AdapterResponse:
        return await self.post(f"food/v1/orders/{order_id}/rating", token=token, payload={"stars": rating, "comment": comment}, idempotency_key=key)

    async def rate_restaurant(self, *_args: object, **_kwargs: object) -> AdapterResponse:
        raise RuntimeError("DiddiFood restaurant rating contract is not available")
