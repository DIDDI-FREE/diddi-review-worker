import httpx
import pytest

from app.bootstrap import build_runtime
from app.config.settings import Settings


def settings() -> Settings:
    return Settings(
        review_accounts_json='[{"reviewer_user_id":"u1","tested_role":"passenger","counter_role":"driver","counter_user_id":"u2","product":"diddigo"}]',
        diddigo_base_url="https://go.test",
        diddisend_base_url="https://send.test",
        diddifoood_base_url="https://food.test",
    )


def test_bootstrap_builds_all_read_only_pollers():
    async_client = httpx.AsyncClient()
    runtime = build_runtime(settings(), async_client)
    assert runtime.registry.bindings()[0].counter_user_id == "u2"
    assert runtime.go.client.base_url == "https://go.test"
    assert runtime.send.client.base_url == "https://send.test"
    assert runtime.food.client.base_url == "https://food.test"


def test_bootstrap_rejects_empty_registry():
    with pytest.raises(ValueError, match="no enabled review"):
        build_runtime(Settings(review_accounts_json="[]"), httpx.AsyncClient())
