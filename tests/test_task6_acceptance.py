from unittest.mock import AsyncMock

import pytest

from app.auth.jwt import ReviewClaims
from app.orchestration.go_workflow import GoDriverWorkflow
from app.orchestration.reactive import (
    AccountBinding,
    ObservedTrigger,
    ReactiveCoordinator,
    TriggerKind,
)
from app.orchestration.session import ReactiveSession, SessionState, SessionStatus
from app.orchestration.terminal import should_stop


def test_tache6_non_review_binding_is_ignored():
    coordinator = ReactiveCoordinator([AccountBinding("review", "passenger", "driver", "driver", "diddigo")])
    trigger = ObservedTrigger("e", TriggerKind.CONSUMER_RESOURCE_CREATED, "diddigo", "passenger", "other", "r", "v")
    assert coordinator.react(trigger) is None


def test_tache6_one_trigger_only():
    coordinator = ReactiveCoordinator([AccountBinding("review", "passenger", "driver", "driver", "diddigo")])
    trigger = ObservedTrigger("e", TriggerKind.CONSUMER_RESOURCE_CREATED, "diddigo", "passenger", "review", "r", "v")
    assert coordinator.react(trigger) is not None
    assert coordinator.react(trigger) is None


def test_tache6_waits_for_reviewer():
    session = ReactiveSession(SessionState("s"), ReactiveCoordinator([AccountBinding("review", "passenger", "driver", "driver", "diddigo")]))
    trigger = ObservedTrigger("e", TriggerKind.CONSUMER_RESOURCE_CREATED, "diddigo", "passenger", "review", "r", "v")
    assert session.observe(trigger)
    session.wait_for_reviewer("pin")
    assert session.state.status is SessionStatus.WAITING_REVIEWER


def test_tache6_stops_on_cancel():
    assert should_stop("CANCELLED")


@pytest.mark.asyncio
async def test_tache6_response_lost_is_safe_to_retry_by_state():
    actions = type("Actions", (), {"accept_ride": AsyncMock(), "arrive": AsyncMock(), "start": AsyncMock(), "update_status": AsyncMock()})()
    workflow = GoDriverWorkflow(actions)
    assert await workflow.advance("r", token="t", server_status="REQUESTED", start_code=None, key_prefix="k")
    assert await workflow.advance("r", token="t", server_status="ACCEPTED", start_code=None, key_prefix="k")
    assert actions.accept_ride.await_count == 1
    assert actions.arrive.await_count == 1


def test_tache6_review_claim_shape():
    assert ReviewClaims("review", "passenger", True).is_review_account is True
