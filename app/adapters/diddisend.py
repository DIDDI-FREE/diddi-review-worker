from app.adapters.base import AdapterResponse, HttpAdapter


class DiddiSendAdapter(HttpAdapter):
    async def rate_sender(self, delivery_id: str, *, token: str, rating: int, comment: str | None, key: str) -> AdapterResponse:
        return await self.post(f"v1/deliveries/{delivery_id}/rate", token=token, payload={"rating": rating, "comment": comment}, idempotency_key=key)

    async def rate_courier(self, delivery_id: str, *, token: str, rating: int, comment: str | None, key: str) -> AdapterResponse:
        return await self.post(f"v1/courier/deliveries/{delivery_id}/rate", token=token, payload={"rating": rating, "comment": comment}, idempotency_key=key)
