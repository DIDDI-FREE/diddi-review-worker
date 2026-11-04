from app.orchestration.reactive import (
    AccountBinding,
    ObservedTrigger,
    ReactiveCoordinator,
    TriggerKind,
)
from app.orchestration.session import ReactiveSession, SessionState, SessionStatus


def make_session():
    return ReactiveSession(
        SessionState("s1"),
        ReactiveCoordinator([AccountBinding("reviewer", "passenger", "driver", "driver", "diddigo")]),
    )


def trigger(version="v1"):
    return ObservedTrigger("e1", TriggerKind.CONSUMER_RESOURCE_CREATED, "diddigo", "passenger", "reviewer", "ride-1", version)


def test_session_accepts_one_trigger_and_rejects_repeats():
    session = make_session()
    assert session.observe(trigger()) is True
    assert session.observe(trigger()) is False
    assert session.state.status is SessionStatus.ACTIVE
    assert session.state.resource_ids == ["ride-1"]


def test_session_waits_for_reviewer_instead_of_substituting():
    session = make_session()
    session.observe(trigger())
    session.wait_for_reviewer("reviewer_must_start")
    assert session.state.status is SessionStatus.WAITING_REVIEWER
    assert session.state.current_step == "reviewer_must_start"


def test_terminal_session_stops_until_explicit_rearm():
    session = make_session()
    session.observe(trigger())
    session.finish()
    assert session.observe(trigger("v2")) is False
    session.rearm()
    assert session.observe(trigger("v2")) is True
