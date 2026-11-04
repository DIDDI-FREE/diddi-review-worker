import httpx
import pytest

from app.adapters.diddifood import DiddiFoodAdapter
from app.adapters.diddisend import DiddiSendAdapter


@pytest.mark.asyncio
async def test_send_consumer_reads_created_delivery_by_id():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "delivery-1", "status": "created"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await DiddiSendAdapter("send", "http://send", client).get_delivery("delivery-1", token="jwt")
    assert result["id"] == "delivery-1"


@pytest.mark.asyncio
async def test_food_consumer_reads_created_order_by_id():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "order-1", "status": "created"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await DiddiFoodAdapter("food", "http://food", client).get_order("order-1", token="jwt")
    assert result["id"] == "order-1"
