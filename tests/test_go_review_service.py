from unittest.mock import AsyncMock

import pytest

from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.observation.pollers import GoPoller
from app.persistence.event_ledger import InMemoryEventLedger
from app.services.go_review import GoReviewService


@pytest.mark.asyncio
async def test_go_service_uses_passenger_observation_and_driver_actions():
    registry = ReviewAccountRegistry.from_json('[{"reviewer_user_id":"p","tested_role":"passenger","counter_role":"driver","counter_user_id":"d","product":"diddigo"}]')
    client = type("Client", (), {"get": AsyncMock(return_value={"items": [{"id": "r1", "status": "REQUESTED"}]})})()
    poller = GoPoller(client)
    adapter = type("Adapter", (), {"get_ride": AsyncMock(return_value={"id": "r1", "status": "REQUESTED", "pickup": {}, "dropoff": {}}), "accept_ride": AsyncMock(), "arrive": AsyncMock(), "start": AsyncMock(), "update_status": AsyncMock(), "push_locations": AsyncMock()})()
    service = GoReviewService(registry=registry, tokens=ReviewTokenCache(lambda _: _token()), poller=poller, adapter=adapter, ledger=InMemoryEventLedger())
    assert await service.run_once() == 1
    assert adapter.accept_ride.await_count == 1


async def _token():
    return "jwt"
