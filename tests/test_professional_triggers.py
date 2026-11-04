from unittest.mock import AsyncMock

import pytest

from app.orchestration.professional_triggers import ProfessionalTriggerRunner


@pytest.mark.asyncio
@pytest.mark.parametrize("product", ["diddigo", "diddisend", "diddifood"])
async def test_tache3_creates_one_request_on_new_availability(product):
    create = AsyncMock(return_value={"id": f"{product}-1"})
    runner = ProfessionalTriggerRunner()
    assert await runner.on_availability(product=product, user_id="worker-1", available=False, create_request=create) is None
    result = await runner.on_availability(product=product, user_id="worker-1", available=True, create_request=create)
    assert result["id"] == f"{product}-1"
    assert await runner.on_availability(product=product, user_id="worker-1", available=True, create_request=create) is None
    create.assert_awaited_once()
