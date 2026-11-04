from unittest.mock import AsyncMock

import pytest

from app.orchestration.go_workflow import GoDriverWorkflow


@pytest.mark.asyncio
async def test_go_driver_workflow_follows_server_state_only():
    actions = type("Actions", (), {
        "accept_ride": AsyncMock(), "arrive": AsyncMock(), "start": AsyncMock(), "update_status": AsyncMock()
    })()
    flow = GoDriverWorkflow(actions)
    assert await flow.advance("r1", token="jwt", server_status="REQUESTED", start_code=None, key_prefix="s")
    assert actions.accept_ride.await_count == 1
    assert actions.start.await_count == 0


@pytest.mark.asyncio
async def test_go_workflow_waits_for_reviewer_pin():
    actions = type("Actions", (), {"accept_ride": AsyncMock(), "arrive": AsyncMock(), "start": AsyncMock(), "update_status": AsyncMock()})()
    assert await GoDriverWorkflow(actions).advance("r1", token="jwt", server_status="ARRIVED", start_code=None, key_prefix="s") is False
    assert actions.start.await_count == 0
