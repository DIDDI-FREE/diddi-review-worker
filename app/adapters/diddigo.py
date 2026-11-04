from app.adapters.base import AdapterResponse, HttpAdapter


class DiddiGoAdapter(HttpAdapter):
    async def rate_ride(self, ride_id: str, *, token: str, rating: int, comment: str | None, key: str) -> AdapterResponse:
        return await self.post(f"v1/rides/{ride_id}/rating", token=token, payload={"rating": rating, "comment": comment}, idempotency_key=key)
