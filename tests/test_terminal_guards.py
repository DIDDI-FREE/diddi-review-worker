from app.orchestration.terminal import should_stop, should_wait_for_reviewer


def test_tache4_stops_terminal_states():
    assert should_stop("CANCELLED")
    assert should_stop("COMPLETED")
    assert not should_stop("IN_PROGRESS")


def test_tache4_waits_for_reviewer_input():
    assert should_wait_for_reviewer("ARRIVED", required_value=None)
    assert not should_wait_for_reviewer("ARRIVED", required_value="1234")
