from typing import Any

import httpx


class ReadOnlyHttpClient:
    """Small read-only client passed to product pollers."""

    def __init__(self, base_url: str, client: httpx.AsyncClient) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client

    async def get(self, path: str, *, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self.client.get(
            f"{self.base_url}/{path.lstrip('/')}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        response.raise_for_status()
        return response.json() if response.content else {}
