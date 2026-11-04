from app.adapters.base import AdapterResponse, HttpAdapter


class DiddiGoAdapter(HttpAdapter):
    async def get_ride(self, ride_id: str, *, token: str) -> dict:
        return await self.get(f"v1/rides/{ride_id}", token=token)

    async def estimate_ride(self, *, token: str, pickup: dict, dropoff: dict, key: str) -> AdapterResponse:
        payload = {"pickup": pickup, "dropoff": dropoff, "vehicle_category": "standard", "comfort_level": "standard"}
        return await self.post("v1/rides/pricing/estimate", token=token, payload=payload, idempotency_key=key)

    async def create_ride(self, *, token: str, quote_id: str, key: str) -> AdapterResponse:
        return await self.post("v1/rides", token=token, payload={"quote_id": quote_id, "payment_method": "cash"}, idempotency_key=key)

    async def update_status(self, ride_id: str, *, token: str, status: str, key: str) -> AdapterResponse:
        return await self.patch(f"v1/rides/{ride_id}/status", token=token, payload={"status": status}, idempotency_key=key)

    async def accept_ride(self, ride_id: str, *, token: str, key: str) -> AdapterResponse:
        return await self.post(f"v1/rides/{ride_id}/accept", token=token, payload={}, idempotency_key=key)

    async def arrive(self, ride_id: str, *, token: str, key: str) -> AdapterResponse:
        return await self.post(f"v1/rides/{ride_id}/arrive", token=token, payload={}, idempotency_key=key)

    async def start(self, ride_id: str, *, token: str, code: str, key: str) -> AdapterResponse:
        return await self.post(f"v1/rides/{ride_id}/start", token=token, payload={"code": code}, idempotency_key=key)

    async def push_locations(self, ride_id: str, *, token: str, samples: list[dict], key: str, batch_id: str | None = None) -> AdapterResponse:
        payload = {"samples": samples}
        if batch_id is not None:
            payload["batch_id"] = batch_id
        return await self.post(f"v1/rides/{ride_id}/location-samples", token=token, payload=payload, idempotency_key=key)

    async def rate_ride(self, ride_id: str, *, token: str, rating: int, comment: str | None, key: str) -> AdapterResponse:
        return await self.post(f"v1/rides/{ride_id}/rating", token=token, payload={"rating": rating, "comment": comment}, idempotency_key=key)
