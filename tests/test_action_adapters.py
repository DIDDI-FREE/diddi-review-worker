import httpx
import pytest

from app.adapters.diddigo import DiddiGoAdapter
from app.adapters.diddisend import DiddiSendAdapter
from app.adapters.diddifood import DiddiFoodAdapter


@pytest.mark.asyncio
async def test_normal_counter_role_endpoints_use_idempotency():
    calls = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path, request.headers["idempotency-key"]))
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await DiddiGoAdapter("go", "http://go", client).accept_ride("r1", token="t", key="k1")
        await DiddiSendAdapter("send", "http://send", client).accept("d1", token="t", key="k2")
        await DiddiFoodAdapter("food", "http://food", client).mark_ready("rest", "o1", token="t", key="k3")
    assert calls == [("POST", "/v1/rides/r1/accept", "k1"), ("POST", "/v1/deliveries/d1/accept", "k2"), ("POST", "/food/v1/restaurants/rest/orders/o1/ready", "k3")]
