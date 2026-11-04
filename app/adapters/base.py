from dataclasses import dataclass
from typing import Any

import httpx


class AdapterError(Exception):
    def __init__(self, service: str, status: int, code: str, retryable: bool = False) -> None:
        super().__init__(f"{service} returned {status}: {code}")
        self.service, self.status, self.code, self.retryable = service, status, code, retryable


@dataclass(frozen=True)
class AdapterResponse:
    status: int
    payload: dict[str, Any]


class HttpAdapter:
    def __init__(self, service: str, base_url: str, client: httpx.AsyncClient) -> None:
        self.service, self.base_url, self.client = service, base_url.rstrip("/"), client

    async def post(self, path: str, *, token: str, payload: dict[str, Any], idempotency_key: str) -> AdapterResponse:
        response = await self.client.post(
            f"{self.base_url}/{path.lstrip('/')}",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": idempotency_key},
            json=payload,
        )
        if response.status_code >= 400:
            body = response.json() if response.content else {}
            code = body.get("code") or body.get("error", {}).get("code") or f"HTTP_{response.status_code}"
            raise AdapterError(self.service, response.status_code, str(code), response.status_code >= 500)
        return AdapterResponse(response.status_code, response.json() if response.content else {})

    async def get(self, path: str, *, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self.client.get(
            f"{self.base_url}/{path.lstrip('/')}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        if response.status_code >= 400:
            body = response.json() if response.content else {}
            code = body.get("code") or body.get("error", {}).get("code") or f"HTTP_{response.status_code}"
            raise AdapterError(self.service, response.status_code, str(code), response.status_code >= 500)
        return response.json() if response.content else {}

    async def patch(self, path: str, *, token: str, payload: dict[str, Any], idempotency_key: str) -> AdapterResponse:
        response = await self.client.patch(
            f"{self.base_url}/{path.lstrip('/')}",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": idempotency_key},
            json=payload,
        )
        if response.status_code >= 400:
            raise AdapterError(self.service, response.status_code, f"HTTP_{response.status_code}", response.status_code >= 500)
        return AdapterResponse(response.status_code, response.json() if response.content else {})
