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
