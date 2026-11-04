from unittest.mock import AsyncMock

import pytest

from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.config.settings import Settings
from app.observation.pollers import FoodPoller
from app.persistence.event_ledger import InMemoryEventLedger
from app.services.food_professional import FoodProfessionalService

REGISTRY = '[{"reviewer_user_id":"rest","tested_role":"restaurant","counter_role":"customer","counter_user_id":"client","product":"diddifood","counter_only":true}]'


async def _token(_: str = "") -> str:
    return "jwt"


def _service(active_sequence: list[bool]) -> tuple:
    registry = ReviewAccountRegistry.from_json(REGISTRY)
    client = type("Client", (), {"get": AsyncMock(side_effect=[[{"restaurant": {"id": "r1", "status": "active" if v else "temporarily_closed"}, "role": "manager"}] for v in active_sequence])})()
    poller = FoodPoller(client)
    adapter = type("Adapter", (), {
        "get_menu": AsyncMock(return_value={"restaurant_id": "r1", "items": [{"id": "dish-1"}]}),
        "place_order": AsyncMock(return_value=type("R", (), {"status": 201, "payload": {"id": "o1"}})()),
    })()
    service = FoodProfessionalService(registry=registry, tokens=ReviewTokenCache(_token), poller=poller, adapter=adapter, settings=Settings(), ledger=InMemoryEventLedger())
    return service, adapter


@pytest.mark.asyncio
async def test_food_pro_does_not_fire_on_startup_open():
    service, adapter = _service([True])
    assert await service.run_once() == 0
    assert adapter.place_order.await_count == 0


@pytest.mark.asyncio
async def test_food_pro_places_one_order_on_open_transition():
    service, adapter = _service([False, True, True])
    assert await service.run_once() == 0  # prime (closed baseline)
    assert await service.run_once() == 1  # closed -> active: order once
    assert await service.run_once() == 0  # still active: no duplicate
    assert adapter.place_order.await_count == 1
    assert adapter.place_order.await_args.kwargs["items"] == [{"dish_id": "dish-1", "quantity": 1}]
