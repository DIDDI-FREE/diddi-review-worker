"""Idempotency ledger boundary for observed review triggers."""

from threading import Lock


class InMemoryEventLedger:
    """Reference implementation; production must replace storage with SQL/Redis."""

    def __init__(self) -> None:
        self._claimed: set[str] = set()
        self._terminal: set[str] = set()
        self._lock = Lock()

    def claim(self, event_key: str) -> bool:
        """Atomically claim an event. Returns false for duplicates/terminal events."""
        with self._lock:
            if event_key in self._claimed or event_key in self._terminal:
                return False
            self._claimed.add(event_key)
            return True

    def mark_terminal(self, event_key: str) -> None:
        with self._lock:
            self._terminal.add(event_key)

    def is_claimed(self, event_key: str) -> bool:
        with self._lock:
            return event_key in self._claimed
