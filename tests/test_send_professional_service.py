from unittest.mock import AsyncMock

import pytest

from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.config.settings import Settings
from app.observation.pollers import SendPoller
from app.persistence.event_ledger import InMemoryEventLedger
from app.services.send_professional import SendProfessionalService

REGISTRY = '[{"reviewer_user_id":"cour","tested_role":"courier","counter_role":"sender","counter_user_id":"client","product":"diddisend","counter_only":true}]'


async def _token(_: str = "") -> str:
    return "jwt"


def _service(online_sequence: list[bool]) -> tuple:
    registry = ReviewAccountRegistry.from_json(REGISTRY)
    client = type("Client", (), {"get": AsyncMock(side_effect=[{"courier": {"availability_status": "online" if v else "offline"}} for v in online_sequence])})()
    poller = SendPoller(client)
    adapter = type("Adapter", (), {"create_delivery": AsyncMock(return_value=type("R", (), {"status": 201, "payload": {"delivery": {"id": "d1"}}})())})()
    service = SendProfessionalService(registry=registry, tokens=ReviewTokenCache(_token), poller=poller, adapter=adapter, settings=Settings(), ledger=InMemoryEventLedger())
    return service, adapter


@pytest.mark.asyncio
async def test_send_pro_does_not_fire_on_startup_online():
    service, adapter = _service([True])
    assert await service.run_once() == 0
    assert adapter.create_delivery.await_count == 0


@pytest.mark.asyncio
async def test_send_pro_creates_one_delivery_on_transition():
    service, adapter = _service([False, True, True])
    assert await service.run_once() == 0  # prime (offline baseline)
    assert await service.run_once() == 1  # offline -> online: create one
    assert await service.run_once() == 0  # still online: no duplicate
    assert adapter.create_delivery.await_count == 1
    # the client (counter) account is the sender of the created delivery
    assert adapter.create_delivery.await_args.kwargs["sender_user_id"] == "client"
