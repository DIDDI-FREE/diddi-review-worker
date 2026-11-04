import pytest

from app.observation.pollers import FoodPoller, GoPoller, PollContext, SendPoller


class FakeReadClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    async def get(self, path, *, token, params=None):
        self.calls.append((path, token, params))
        return self.payload


@pytest.mark.asyncio
async def test_go_poller_is_read_only_and_normalizes_rides():
    client = FakeReadClient({"items": [{"id": "ride-1", "status": "requested"}]})
    events = await GoPoller(client).rides(PollContext("reviewer", "jwt"))
    assert events[0].resource_id == "ride-1"
    assert client.calls[0][0] == "v1/rides"


@pytest.mark.asyncio
async def test_send_poller_reads_offers_only():
    client = FakeReadClient({"items": [{"delivery_id": "delivery-1", "status": "offered"}]})
    events = await SendPoller(client).offers(PollContext("courier", "jwt"))
    assert events[0].resource_id == "delivery-1"


@pytest.mark.asyncio
async def test_food_poller_reads_restaurant_orders():
    client = FakeReadClient({"items": [{"id": "order-1", "status": "created"}]})
    events = await FoodPoller(client).restaurant_orders(PollContext("restaurant", "jwt"), "restaurant-1")
    assert events[0].resource_id == "order-1"
