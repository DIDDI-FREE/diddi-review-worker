from unittest.mock import AsyncMock

import pytest

from app.orchestration.send_workflow import SendCourierWorkflow


@pytest.mark.asyncio
async def test_send_waits_for_location_and_pin():
    actions = type("Actions", (), {"accept": AsyncMock(), "pickup": AsyncMock(), "deliver": AsyncMock()})()
    flow = SendCourierWorkflow(actions)
    assert await flow.advance("d1", token="jwt", server_status="ACCEPTED", location=None, recorded_at=None, delivery_pin=None, key_prefix="s") is False
    assert actions.pickup.await_count == 0


@pytest.mark.asyncio
async def test_send_accepts_then_delivers_with_required_data():
    actions = type("Actions", (), {"accept": AsyncMock(), "pickup": AsyncMock(), "deliver": AsyncMock()})()
    flow = SendCourierWorkflow(actions)
    assert await flow.advance("d1", token="jwt", server_status="OFFERED", location=None, recorded_at=None, delivery_pin=None, key_prefix="s")
    assert await flow.advance("d1", token="jwt", server_status="PICKED_UP", location={"lat": 5, "lng": 6, "address": "test"}, recorded_at="2026-11-04T00:00:00Z", delivery_pin="1234", key_prefix="s")
    assert actions.accept.await_count == 1
    assert actions.deliver.await_count == 1
