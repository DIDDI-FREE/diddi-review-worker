from app.adapters.base import AdapterResponse, HttpAdapter


class DiddiFoodAdapter(HttpAdapter):
    async def get_order(self, order_id: str, *, token: str) -> dict:
        return await self.get(f"food/v1/orders/{order_id}", token=token)

    async def get_menu(self, restaurant_id: str, *, token: str) -> dict:
        return await self.get(f"food/v1/restaurants/{restaurant_id}/menu", token=token)

    async def place_order(self, restaurant_id: str, *, token: str, items: list[dict], dropoff: dict, key: str) -> AdapterResponse:
        payload = {
            "items": items,
            "payment_method": "cash_on_delivery",
            "pickup_mode": "delivery",
            "dropoff_address": dropoff.get("address", ""),
            "dropoff_latitude": dropoff.get("lat"),
            "dropoff_longitude": dropoff.get("lng"),
            "recipient_name": "Review Customer",
            "recipient_phone": "+2250700000000",
        }
        return await self.post(f"food/v1/restaurants/{restaurant_id}/orders", token=token, payload=payload, idempotency_key=key)

    async def accept_order(self, restaurant_id: str, order_id: str, *, token: str, prep_minutes: int, key: str) -> AdapterResponse:
        return await self.post(f"food/v1/restaurants/{restaurant_id}/orders/{order_id}/accept", token=token, payload={"prep_minutes": prep_minutes}, idempotency_key=key)

    async def mark_ready(self, restaurant_id: str, order_id: str, *, token: str, key: str) -> AdapterResponse:
        return await self.post(f"food/v1/restaurants/{restaurant_id}/orders/{order_id}/ready", token=token, payload={}, idempotency_key=key)

    async def rate_customer(self, order_id: str, *, token: str, rating: int, comment: str | None, key: str) -> AdapterResponse:
        return await self.post(f"food/v1/orders/{order_id}/rating", token=token, payload={"stars": rating, "comment": comment}, idempotency_key=key)

    async def rate_restaurant(self, *_args: object, **_kwargs: object) -> AdapterResponse:
        raise RuntimeError("DiddiFood restaurant rating contract is not available")
