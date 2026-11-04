from app.orchestration.reactive import (
    AccountBinding,
    ObservedTrigger,
    ReactiveCoordinator,
    TriggerKind,
)


def coordinator() -> ReactiveCoordinator:
    return ReactiveCoordinator([
        AccountBinding("reviewer", "passenger", "driver", "driver-review", "diddigo"),
    ])


def test_no_trigger_creates_no_reaction() -> None:
    assert coordinator().react(ObservedTrigger("e1", TriggerKind.CONSUMER_RESOURCE_CREATED, "diddigo", "passenger", "other", "r1")) is None


def test_explicit_review_trigger_reacts_once() -> None:
    c = coordinator()
    trigger = ObservedTrigger("e1", TriggerKind.CONSUMER_RESOURCE_CREATED, "diddigo", "passenger", "reviewer", "r1", "v1")
    reaction = c.react(trigger)
    assert reaction is not None
    assert reaction.binding.counter_user_id == "driver-review"
    assert c.react(trigger) is None


def test_waits_for_resource_on_professional_availability() -> None:
    trigger = ObservedTrigger("e1", TriggerKind.PROFESSIONAL_AVAILABLE, "diddigo", "passenger", "reviewer")
    assert coordinator().react(trigger) is None


def test_terminal_trigger_stops_future_action() -> None:
    c = coordinator()
    trigger = ObservedTrigger("e1", TriggerKind.CONSUMER_RESOURCE_CREATED, "diddigo", "passenger", "reviewer", "r1", "v1")
    c.mark_terminal(trigger)
    assert c.react(trigger) is None
