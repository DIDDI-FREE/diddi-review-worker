from unittest.mock import AsyncMock

import pytest

from app.orchestration.food_workflow import FoodRestaurantWorkflow


@pytest.mark.asyncio
async def test_food_waits_for_prep_minutes():
    actions = type("Actions", (), {"accept_order": AsyncMock(), "mark_ready": AsyncMock()})()
    assert await FoodRestaurantWorkflow(actions).advance("rest", "order", token="jwt", server_status="PENDING", prep_minutes=None, key_prefix="s") is False
    assert actions.accept_order.await_count == 0


@pytest.mark.asyncio
async def test_food_accepts_and_marks_ready():
    actions = type("Actions", (), {"accept_order": AsyncMock(), "mark_ready": AsyncMock()})()
    flow = FoodRestaurantWorkflow(actions)
    assert await flow.advance("rest", "order", token="jwt", server_status="PENDING", prep_minutes=20, key_prefix="s")
    assert await flow.advance("rest", "order", token="jwt", server_status="PREPARING", prep_minutes=20, key_prefix="s")
    assert actions.accept_order.await_count == 1
    assert actions.mark_ready.await_count == 1
