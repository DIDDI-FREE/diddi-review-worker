from app.adapters.base import AdapterResponse, HttpAdapter


class DiddiSendAdapter(HttpAdapter):
    async def get_delivery(self, delivery_id: str, *, token: str) -> dict:
        return await self.get(f"v1/deliveries/{delivery_id}", token=token)

    async def accept(self, delivery_id: str, *, token: str, key: str) -> AdapterResponse:
        return await self.post(f"v1/deliveries/{delivery_id}/accept", token=token, payload={}, idempotency_key=key)

    async def pickup(self, delivery_id: str, *, token: str, location: dict, recorded_at: str, key: str) -> AdapterResponse:
        return await self.post(f"v1/deliveries/{delivery_id}/pickup", token=token, payload={"location": location, "recorded_at": recorded_at}, idempotency_key=key)

    async def deliver(self, delivery_id: str, *, token: str, location: dict, recorded_at: str, delivery_pin: str, key: str, photo_file_id: str | None = None, signature_file_id: str | None = None, note: str | None = None) -> AdapterResponse:
        payload = {"location": location, "recorded_at": recorded_at, "delivery_pin": delivery_pin}
        for name, value in (("photo_file_id", photo_file_id), ("signature_file_id", signature_file_id), ("note", note)):
            if value is not None:
                payload[name] = value
        return await self.post(f"v1/deliveries/{delivery_id}/deliver", token=token, payload=payload, idempotency_key=key)

    async def rate_sender(self, delivery_id: str, *, token: str, rating: int, comment: str | None, key: str) -> AdapterResponse:
        return await self.post(f"v1/deliveries/{delivery_id}/rate", token=token, payload={"rating": rating, "comment": comment}, idempotency_key=key)

    async def rate_courier(self, delivery_id: str, *, token: str, rating: int, comment: str | None, key: str) -> AdapterResponse:
        return await self.post(f"v1/courier/deliveries/{delivery_id}/rate", token=token, payload={"rating": rating, "comment": comment}, idempotency_key=key)
