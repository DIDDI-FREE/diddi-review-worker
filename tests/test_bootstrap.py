import httpx
import pytest

from app.auth.jwt import ReviewClaims
from app.bootstrap import build_runtime
from app.config.settings import Settings


def settings() -> Settings:
    return Settings(
        review_accounts_json='[{"reviewer_user_id":"u1","tested_role":"passenger","counter_role":"driver","counter_user_id":"u2","product":"diddigo","email":"u1@example.com","otp":"123456"}]',
        diddigo_base_url="https://go.test",
        diddisend_base_url="https://send.test",
        diddifood_base_url="https://food.test",
    )


def test_bootstrap_builds_all_read_only_pollers():
    async_client = httpx.AsyncClient()
    runtime = build_runtime(settings(), async_client)
    assert runtime.registry.bindings()[0].counter_user_id == "u2"
    assert runtime.go.client.base_url == "https://go.test"
    assert runtime.send.client.base_url == "https://send.test"
    assert runtime.food.client.base_url == "https://food.test"


@pytest.mark.asyncio
async def test_bootstrap_resolves_only_explicit_account(monkeypatch):
    settings_value = settings()
    runtime = build_runtime(settings_value, httpx.AsyncClient())
    async def issue(_, __):
        return "jwt"
    monkeypatch.setattr("app.auth.token_provider.DiddiFreeIDTokenProvider.issue_access_token", issue)
    monkeypatch.setattr(
        "app.adapters.diddifreeid.DiddiFreeIDAdapter.validate_actor_token",
        lambda _, token: ReviewClaims("u1", "passenger", True),
    )
    assert await runtime.tokens.get("u1") == "jwt"
    with pytest.raises(ValueError, match="account is not explicitly configured"):
        await runtime.tokens.get("unknown")


def test_bootstrap_rejects_empty_registry():
    with pytest.raises(ValueError, match="no enabled review"):
        build_runtime(Settings(review_accounts_json="[]"), httpx.AsyncClient())


@pytest.mark.asyncio
async def test_bootstrap_rejects_non_review_token(monkeypatch):
    runtime = build_runtime(settings(), httpx.AsyncClient())

    async def issue(_, __):
        return "jwt"

    monkeypatch.setattr("app.auth.token_provider.DiddiFreeIDTokenProvider.issue_access_token", issue)
    monkeypatch.setattr(
        "app.adapters.diddifreeid.DiddiFreeIDAdapter.validate_actor_token",
        lambda _, token: (_ for _ in ()).throw(ValueError("token is not a review account token")),
    )
    with pytest.raises(ValueError, match="not a review account"):
        await runtime.tokens.get("u1")
