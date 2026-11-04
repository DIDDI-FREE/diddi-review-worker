import pytest

from app.config.review_accounts import ReviewAccountRegistry


def test_registry_only_returns_enabled_explicit_bindings():
    registry = ReviewAccountRegistry.from_json(
        '[{"reviewer_user_id":"u1","tested_role":"passenger","counter_role":"driver","counter_user_id":"u2","product":"diddigo"},'
        '{"reviewer_user_id":"u3","tested_role":"customer","counter_role":"restaurant","counter_user_id":"u4","product":"diddifood","enabled":false}]'
    )
    assert len(registry.bindings()) == 1
    assert registry.bindings()[0].counter_user_id == "u2"


def test_registry_rejects_invalid_json():
    with pytest.raises(ValueError):
        ReviewAccountRegistry.from_json("not-json")


def test_counter_only_account_provides_credentials_without_trigger_binding():
    registry = ReviewAccountRegistry.from_json(
        '[{"reviewer_user_id":"p","tested_role":"passenger","counter_role":"driver","counter_user_id":"d","product":"diddigo"},'
        '{"reviewer_user_id":"d","tested_role":"driver","counter_role":"passenger","counter_user_id":"p","product":"diddigo","counter_only":true}]'
    )
    assert len(registry.bindings()) == 1
    assert registry.accounts[1].counter_only is True
