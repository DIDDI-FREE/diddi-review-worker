from unittest.mock import AsyncMock

import pytest

from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.config.settings import Settings
from app.observation.pollers import IdentityPoller
from app.persistence.event_ledger import InMemoryEventLedger
from app.services.go_professional import GoProfessionalService

REGISTRY = '[{"reviewer_user_id":"drv","tested_role":"driver","counter_role":"passenger","counter_user_id":"client","product":"diddigo","counter_only":true}]'


async def _token(_: str = "") -> str:
    return "jwt"


def _service(online_sequence: list[bool]) -> tuple:
    registry = ReviewAccountRegistry.from_json(REGISTRY)
    client = type("Client", (), {"get": AsyncMock(side_effect=[{"capabilities": [{"operational_status": "online" if v else "offline"}]} for v in online_sequence])})()
    poller = IdentityPoller(client)
    adapter = type("Adapter", (), {
        "estimate_ride": AsyncMock(return_value=type("R", (), {"status": 200, "payload": {"quote_id": "q1"}})()),
        "create_ride": AsyncMock(return_value=type("R", (), {"status": 201, "payload": {"ride_id": "r1"}})()),
    })()
    service = GoProfessionalService(registry=registry, tokens=ReviewTokenCache(_token), poller=poller, adapter=adapter, settings=Settings(), ledger=InMemoryEventLedger())
    return service, adapter


@pytest.mark.asyncio
async def test_go_pro_does_not_fire_on_startup_online():
    service, adapter = _service([True])
    assert await service.run_once() == 0
    assert adapter.create_ride.await_count == 0


@pytest.mark.asyncio
async def test_go_pro_requests_one_ride_on_transition():
    service, adapter = _service([False, True, True])
    assert await service.run_once() == 0  # prime (offline baseline)
    assert await service.run_once() == 1  # offline -> online: estimate + create
    assert await service.run_once() == 0  # still online: no duplicate
    assert adapter.estimate_ride.await_count == 1
    assert adapter.create_ride.await_count == 1
    assert adapter.create_ride.await_args.kwargs["quote_id"] == "q1"
