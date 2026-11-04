from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import monotonic


@dataclass
class CachedToken:
    value: str
    expires_at: float


class ReviewTokenCache:
    def __init__(self, issuer: Callable[[str], Awaitable[str]], *, ttl_seconds: float = 300) -> None:
        self.issuer = issuer
        self.ttl_seconds = ttl_seconds
        self._tokens: dict[str, CachedToken] = {}

    async def get(self, account_id: str) -> str:
        cached = self._tokens.get(account_id)
        now = monotonic()
        if cached and cached.expires_at > now:
            return cached.value
        token = await self.issuer(account_id)
        self._tokens[account_id] = CachedToken(token, now + self.ttl_seconds)
        return token

    def clear(self, account_id: str) -> None:
        self._tokens.pop(account_id, None)
