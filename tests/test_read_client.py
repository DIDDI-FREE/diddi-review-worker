import httpx
import pytest

from app.observation.clients import ReadOnlyHttpClient


@pytest.mark.asyncio
async def test_read_only_client_sends_get_with_bearer():
    seen = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(200, json={"items": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await ReadOnlyHttpClient("https://go.test", client).get("v1/rides", token="jwt")
    assert result == {"items": []}
    assert seen == {"method": "GET", "auth": "Bearer jwt"}
