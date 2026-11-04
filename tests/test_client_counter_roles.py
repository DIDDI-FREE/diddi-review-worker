from unittest.mock import AsyncMock

import pytest

from app.orchestration.client_counter_roles import ClientCounterRoleRunner


@pytest.mark.asyncio
async def test_tache2_go_uses_driver_counter_role():
    go = type("Go", (), {"accept_ride": AsyncMock(), "arrive": AsyncMock(), "start": AsyncMock(), "update_status": AsyncMock()})()
    runner = ClientCounterRoleRunner(go=go, send=object(), food=object())
    assert await runner.advance_go("ride-1", token="jwt", server_status="REQUESTED", start_code=None, key_prefix="k")
    go.accept_ride.assert_awaited_once()


@pytest.mark.asyncio
async def test_tache2_send_uses_courier_counter_role():
    send = type("Send", (), {"accept": AsyncMock(), "pickup": AsyncMock(), "deliver": AsyncMock()})()
    runner = ClientCounterRoleRunner(go=object(), send=send, food=object())
    assert await runner.advance_send("delivery-1", token="jwt", server_status="OFFERED", location=None, recorded_at=None, delivery_pin=None, key_prefix="k")
    send.accept.assert_awaited_once()


@pytest.mark.asyncio
async def test_tache2_food_uses_restaurant_counter_role():
    food = type("Food", (), {"accept_order": AsyncMock(), "mark_ready": AsyncMock()})()
    runner = ClientCounterRoleRunner(go=object(), send=object(), food=food)
    assert await runner.advance_food("restaurant-1", "order-1", token="jwt", server_status="PENDING", prep_minutes=10, key_prefix="k")
    food.accept_order.assert_awaited_once()
