from concurrent.futures import ThreadPoolExecutor

from app.persistence.event_ledger import InMemoryEventLedger


def test_event_is_claimed_once():
    ledger = InMemoryEventLedger()
    assert ledger.claim("go:ride-1:v1") is True
    assert ledger.claim("go:ride-1:v1") is False


def test_concurrent_claim_has_one_winner():
    ledger = InMemoryEventLedger()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: ledger.claim("send:delivery-1:v1"), range(32)))
    assert sum(results) == 1


def test_terminal_event_cannot_be_claimed():
    ledger = InMemoryEventLedger()
    ledger.mark_terminal("food:order-1:done")
    assert ledger.claim("food:order-1:done") is False
