import json
from dataclasses import dataclass

import httpx

from app.adapters.diddifreeid import DiddiFreeIDAdapter
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
    raw_accounts = settings.review_accounts_json
    if raw_accounts == "[]" and settings.diddigo_passenger_user_id and settings.diddigo_driver_user_id:
        raw_accounts = json.dumps([
            {"reviewer_user_id": settings.diddigo_passenger_user_id, "tested_role": "passenger", "counter_role": "driver", "counter_user_id": settings.diddigo_driver_user_id, "product": "diddigo", "email": settings.diddigo_passenger_email, "otp": settings.diddigo_passenger_otp},
            {"reviewer_user_id": settings.diddigo_driver_user_id, "tested_role": "driver", "counter_role": "passenger", "counter_user_id": settings.diddigo_passenger_user_id, "product": "diddigo", "email": settings.diddigo_driver_email, "otp": settings.diddigo_driver_otp, "counter_only": True},
        ])
    registry = ReviewAccountRegistry.from_json(raw_accounts)
    if not registry.bindings():
        raise ValueError("no enabled review account binding configured")
    provider = DiddiFreeIDTokenProvider(base_url=settings.diddifreeid_base_url, client=client)
    claims_validator = DiddiFreeIDAdapter(
        jwks_url=settings.diddifreeid_jwks_url,
        issuer=settings.diddifreeid_issuer,
        audience=settings.diddifreeid_audience,
        algorithms=settings.algorithms,
    )
    credentials = {account.reviewer_user_id: account.credential() for account in registry.accounts if account.enabled}

    async def issue(account_id: str) -> str:
        credential = credentials.get(account_id)
        if credential is None:
            raise ValueError("account is not explicitly configured")
        token = await provider.issue_access_token(credential)
        claims = claims_validator.validate_actor_token(token)
        if claims.user_id != account_id:
            raise ValueError("token subject does not match configured review account")
        return token

    return ReviewRuntime(
        registry=registry,
        go=GoPoller(ReadOnlyHttpClient(settings.diddigo_base_url, client)),
        send=SendPoller(ReadOnlyHttpClient(settings.diddisend_base_url, client)),
        food=FoodPoller(ReadOnlyHttpClient(settings.diddifoood_base_url, client)),
        tokens=ReviewTokenCache(issue),
    )
