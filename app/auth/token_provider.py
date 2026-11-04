from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class ReviewAccountCredential:
    account_id: str
    phone: str
    otp: str


class DiddiFreeIDTokenProvider:
    """Obtains short-lived user JWTs through the normal OTP flow.

    Credentials must come from a secret manager. The provider never persists or logs
    the OTP/access token and does not support service/admin tokens.
    """

    def __init__(self, *, base_url: str, client: httpx.AsyncClient) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client

    async def issue_access_token(self, credential: ReviewAccountCredential) -> str:
        await self.client.post(f"{self.base_url}/identity/v1/auth/otp/request", json={"phone": credential.phone})
        response = await self.client.post(
            f"{self.base_url}/identity/v1/auth/otp/verify",
            json={"phone": credential.phone, "code": credential.otp},
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("DiddiFreeID did not return a user access token")
        return token
