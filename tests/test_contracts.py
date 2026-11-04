import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.config.settings import get_settings


def test_health_and_authenticated_run() -> None:
    client = TestClient(app)
    assert client.get("/health/live").json() == {"status": "ok"}
    payload = {"scenario": "diddigo-reviews", "steps": [{"key": "ride-passenger", "product": "diddigo", "role": "passenger", "resource_id": "ride-1", "rating": 5}]}
    token = get_settings().runner_service_token
    response = client.post("/v1/runs", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 202
    assert response.json()["status"] == "queued"


def test_run_requires_service_auth() -> None:
    client = TestClient(app)
    response = client.post("/v1/runs", json={"scenario": "diddigo-reviews", "steps": []})
    assert response.status_code == 401


def test_food_restaurant_contract_is_explicitly_blocked() -> None:
    from app.adapters.diddifood import DiddiFoodAdapter

    with pytest.raises(RuntimeError, match="contract"):
        import asyncio
        asyncio.run(DiddiFoodAdapter("food", "http://food", None).rate_restaurant())


def test_invalid_role_is_rejected_before_publishing() -> None:
    client = TestClient(app)
    payload = {"scenario": "diddifood-reviews", "steps": [{"key": "restaurant", "product": "diddifood", "role": "restaurant", "resource_id": "order-1", "rating": 5}]}
    token = get_settings().runner_service_token
    response = client.post("/v1/runs", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
