"""Safety state machine for one reactive Review session."""

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from app.orchestration.reactive import ObservedTrigger, ReactiveCoordinator


class SessionStatus(StrEnum):
    WAITING = "waiting"
    ACTIVE = "active"
    WAITING_REVIEWER = "waiting_reviewer"
    TERMINAL = "terminal"


@dataclass
class SessionState:
    session_id: str
    status: SessionStatus = SessionStatus.WAITING
    trigger_key: str | None = None
    resource_ids: list[str] = field(default_factory=list)
    current_step: str = "waiting_for_trigger"
    engaged_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"session_id": self.session_id, "status": self.status.value, "trigger_key": self.trigger_key, "resource_ids": self.resource_ids, "current_step": self.current_step, "engaged_actions": self.engaged_actions}

    @classmethod
    def from_dict(cls, value: dict) -> "SessionState":
        return cls(value["session_id"], SessionStatus(value["status"]), value.get("trigger_key"), list(value.get("resource_ids", [])), value.get("current_step", "waiting_for_trigger"), list(value.get("engaged_actions", [])))


class JsonSessionStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, state: SessionState) -> None:
        self.path.write_text(json.dumps(state.to_dict()), encoding="utf-8")

    def load(self) -> SessionState | None:
        if not self.path.exists():
            return None
        return SessionState.from_dict(json.loads(self.path.read_text(encoding="utf-8")))


class ReactiveSession:
    def __init__(self, state: SessionState, coordinator: ReactiveCoordinator) -> None:
        self.state = state
        self.coordinator = coordinator

    def observe(self, trigger: ObservedTrigger) -> bool:
        """Accept only a new explicit trigger; never synthesize reviewer actions."""
        if self.state.status is SessionStatus.TERMINAL:
            return False
        key = self.coordinator.event_key(trigger)
        if self.state.trigger_key == key or self.state.status is SessionStatus.ACTIVE:
            return False
        reaction = self.coordinator.react(trigger)
        if reaction is None:
            return False
        self.state.status = SessionStatus.ACTIVE
        self.state.trigger_key = key
        self.state.current_step = "counter_role_pending"
        if trigger.resource_id and trigger.resource_id not in self.state.resource_ids:
            self.state.resource_ids.append(trigger.resource_id)
        return True

    def wait_for_reviewer(self, step: str) -> None:
        if self.state.status is SessionStatus.ACTIVE:
            self.state.status = SessionStatus.WAITING_REVIEWER
            self.state.current_step = step

    def engage_action(self, action: str) -> None:
        if self.state.status not in {SessionStatus.ACTIVE, SessionStatus.WAITING_REVIEWER}:
            return
        if action not in self.state.engaged_actions:
            self.state.engaged_actions.append(action)

    def finish(self) -> None:
        self.state.status = SessionStatus.TERMINAL
        self.state.current_step = "terminal"

    def rearm(self) -> None:
        if self.state.status is SessionStatus.TERMINAL:
            self.state.status = SessionStatus.WAITING
            self.state.trigger_key = None
            self.state.resource_ids.clear()
            self.state.current_step = "waiting_for_trigger"
            self.state.engaged_actions.clear()
