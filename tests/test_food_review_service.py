from unittest.mock import AsyncMock

import pytest

from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.observation.pollers import FoodPoller
from app.persistence.event_ledger import InMemoryEventLedger
from app.services.food_review import FoodReviewService

REGISTRY = '[{"reviewer_user_id":"cust","tested_role":"customer","counter_role":"restaurant","counter_user_id":"rest-staff","product":"diddifood"}]'


async def _token(_: str = "") -> str:
    return "jwt"


def _service(list_status: str, detail_status: str) -> tuple:
    registry = ReviewAccountRegistry.from_json(REGISTRY)
    client = type("Client", (), {"get": AsyncMock(return_value=[{"id": "o1", "status": list_status}])})()
    poller = FoodPoller(client)
    adapter = type("Adapter", (), {
        "get_order": AsyncMock(return_value={"id": "o1", "status": detail_status, "restaurant_id": "rest-1"}),
        "accept_order": AsyncMock(),
        "mark_ready": AsyncMock(),
    })()
    service = FoodReviewService(registry=registry, tokens=ReviewTokenCache(_token), poller=poller, adapter=adapter, ledger=InMemoryEventLedger())
    return service, adapter


@pytest.mark.asyncio
async def test_food_client_restaurant_accepts_placed_order():
    service, adapter = _service("placed", "placed")
    assert await service.run_once() == 1
    assert adapter.accept_order.await_count == 1
    assert adapter.accept_order.await_args.args == ("rest-1", "o1")


@pytest.mark.asyncio
async def test_food_client_restaurant_marks_ready_when_preparing():
    service, adapter = _service("preparing", "preparing")
    assert await service.run_once() == 1
    assert adapter.mark_ready.await_count == 1


@pytest.mark.asyncio
async def test_food_client_skips_ready_and_terminal_orders():
    service, adapter = _service("ready", "ready")
    assert await service.run_once() == 0
    assert adapter.accept_order.await_count == 0
