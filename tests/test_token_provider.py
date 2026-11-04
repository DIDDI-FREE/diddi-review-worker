from unittest.mock import AsyncMock, MagicMock

import pytest

from app.auth.token_provider import DiddiFreeIDTokenProvider, ReviewAccountCredential


@pytest.mark.asyncio
async def test_provider_uses_normal_otp_flow() -> None:
    client = AsyncMock()
    response = MagicMock()
    response.json.return_value = {"access_token": "short-lived"}
    response.raise_for_status = lambda: None
    client.post.side_effect = [AsyncMock(), response]
    provider = DiddiFreeIDTokenProvider(base_url="http://identity", client=client)
    token = await provider.issue_access_token(ReviewAccountCredential("u-1", "+237600000000", "246810"))
    assert token == "short-lived"
    assert client.post.await_count == 2
    assert client.post.await_args_list[1].kwargs["json"]["code"] == "246810"


@pytest.mark.asyncio
async def test_provider_supports_review_email_otp():
    client = AsyncMock()
    response = MagicMock()
    response.json.return_value = {"access_token": "short-lived"}
    response.raise_for_status = lambda: None
    client.post.side_effect = [AsyncMock(), response]
    provider = DiddiFreeIDTokenProvider(base_url="http://identity", client=client)
    await provider.issue_access_token(ReviewAccountCredential("u-1", None, "123456", email="review@example.com"))
    assert client.post.await_args_list[0].kwargs["json"] == {"email": "review@example.com", "channel": "email"}
    assert client.post.await_args_list[1].kwargs["json"] == {"email": "review@example.com", "channel": "email", "code": "123456"}
