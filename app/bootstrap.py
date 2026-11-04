from dataclasses import dataclass

import httpx

from app.auth.token_cache import ReviewTokenCache
from app.auth.token_provider import DiddiFreeIDTokenProvider
from app.config.review_accounts import ReviewAccountRegistry
from app.config.settings import Settings
from app.observation.clients import ReadOnlyHttpClient
from app.observation.pollers import FoodPoller, GoPoller, SendPoller


@dataclass(frozen=True)
class ReviewRuntime:
    registry: ReviewAccountRegistry
    go: GoPoller
    send: SendPoller
    food: FoodPoller
    tokens: ReviewTokenCache


def build_runtime(settings: Settings, client: httpx.AsyncClient) -> ReviewRuntime:
    registry = ReviewAccountRegistry.from_json(settings.review_accounts_json)
    if not registry.bindings():
        raise ValueError("no enabled review account binding configured")
    provider = DiddiFreeIDTokenProvider(base_url=settings.diddifreeid_base_url, client=client)
    credentials = {account.reviewer_user_id: account.credential() for account in registry.accounts if account.enabled}

    async def issue(account_id: str) -> str:
        credential = credentials.get(account_id)
        if credential is None:
            raise ValueError("account is not explicitly configured")
        return await provider.issue_access_token(credential)

    return ReviewRuntime(
        registry=registry,
        go=GoPoller(ReadOnlyHttpClient(settings.diddigo_base_url, client)),
        send=SendPoller(ReadOnlyHttpClient(settings.diddisend_base_url, client)),
        food=FoodPoller(ReadOnlyHttpClient(settings.diddifoood_base_url, client)),
        tokens=ReviewTokenCache(issue),
    )
