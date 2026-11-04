from app.adapters.base import AdapterResponse, HttpAdapter


class DiddiGoAdapter(HttpAdapter):
    async def accept_ride(self, ride_id: str, *, token: str, key: str) -> AdapterResponse:
        return await self.post(f"v1/rides/{ride_id}/accept", token=token, payload={}, idempotency_key=key)

    async def arrive(self, ride_id: str, *, token: str, key: str) -> AdapterResponse:
        return await self.post(f"v1/rides/{ride_id}/arrive", token=token, payload={}, idempotency_key=key)

    async def start(self, ride_id: str, *, token: str, key: str, payload: dict | None = None) -> AdapterResponse:
        return await self.post(f"v1/rides/{ride_id}/start", token=token, payload=payload or {}, idempotency_key=key)

    async def rate_ride(self, ride_id: str, *, token: str, rating: int, comment: str | None, key: str) -> AdapterResponse:
        return await self.post(f"v1/rides/{ride_id}/rating", token=token, payload={"rating": rating, "comment": comment}, idempotency_key=key)
