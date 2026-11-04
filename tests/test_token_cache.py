import pytest

from app.auth.token_cache import ReviewTokenCache


@pytest.mark.asyncio
async def test_token_cache_issues_once_until_expiry():
    calls = []

    async def issue(account_id):
        calls.append(account_id)
        return f"jwt-{len(calls)}"

    cache = ReviewTokenCache(issue, ttl_seconds=60)
    assert await cache.get("u1") == "jwt-1"
    assert await cache.get("u1") == "jwt-1"
    assert calls == ["u1"]


@pytest.mark.asyncio
async def test_token_cache_can_force_refresh():
    count = 0

    async def issue(_):
        nonlocal count
        count += 1
        return f"jwt-{count}"

    cache = ReviewTokenCache(issue)
    assert await cache.get("u1") == "jwt-1"
    cache.clear("u1")
    assert await cache.get("u1") == "jwt-2"
