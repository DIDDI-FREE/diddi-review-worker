from unittest.mock import AsyncMock

import pytest

from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.observation.pollers import SendPoller
from app.persistence.event_ledger import InMemoryEventLedger
from app.services.send_review import SendReviewService

REGISTRY = '[{"reviewer_user_id":"s","tested_role":"sender","counter_role":"courier","counter_user_id":"c","product":"diddisend"}]'


async def _token(_: str = "") -> str:
    return "jwt"


def _service(list_status: str, detail_status: str, adapter_overrides: dict | None = None) -> tuple:
    registry = ReviewAccountRegistry.from_json(REGISTRY)
    client = type("Client", (), {"get": AsyncMock(return_value={"items": [{"id": "d1", "status": list_status}]})})()
    poller = SendPoller(client)
    base = {
        "get_delivery": AsyncMock(return_value={"delivery": {"id": "d1", "status": detail_status, "pickup_location": {"lat": 1.0, "lng": 2.0, "address": "A"}}}),
        "accept": AsyncMock(),
        "pickup": AsyncMock(),
        "deliver": AsyncMock(),
    }
    base.update(adapter_overrides or {})
    adapter = type("Adapter", (), base)()
    service = SendReviewService(registry=registry, tokens=ReviewTokenCache(_token), poller=poller, adapter=adapter, ledger=InMemoryEventLedger())
    return service, adapter


@pytest.mark.asyncio
async def test_send_client_courier_accepts_offer():
    service, adapter = _service("created", "created")
    assert await service.run_once() == 1
    assert adapter.accept.await_count == 1
    assert adapter.pickup.await_count == 0


@pytest.mark.asyncio
async def test_send_client_courier_picks_up_when_assigned():
    service, adapter = _service("assigned", "assigned")
    assert await service.run_once() == 1
    assert adapter.pickup.await_count == 1
    # pickup must carry the delivery's pickup location
    assert adapter.pickup.await_args.kwargs["location"] == {"lat": 1.0, "lng": 2.0}


@pytest.mark.asyncio
async def test_send_client_waits_for_reviewer_pin_before_delivering():
    service, adapter = _service("picked_up", "picked_up")
    assert await service.run_once() == 1
    # No readable review PIN: the runner must not attempt the final delivery.
    assert adapter.deliver.await_count == 0


@pytest.mark.asyncio
async def test_send_client_skips_terminal_delivery():
    service, adapter = _service("delivered", "delivered")
    assert await service.run_once() == 0
    assert adapter.accept.await_count == 0
