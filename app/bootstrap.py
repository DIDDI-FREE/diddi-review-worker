from dataclasses import dataclass

import httpx

from app.config.review_accounts import ReviewAccountRegistry
from app.config.settings import Settings
from app.observation.clients import ReadOnlyHttpClient
from app.observation.pollers import FoodPoller, GoPoller, SendPoller


@dataclass(frozen=True)
class ReviewRuntime:
    registry: ReviewAccountRegistry
    go: GoPoller
    send: SendPoller
    food: FoodPoller


def build_runtime(settings: Settings, client: httpx.AsyncClient) -> ReviewRuntime:
    registry = ReviewAccountRegistry.from_json(settings.review_accounts_json)
    if not registry.bindings():
        raise ValueError("no enabled review account binding configured")
    return ReviewRuntime(
        registry=registry,
        go=GoPoller(ReadOnlyHttpClient(settings.diddigo_base_url, client)),
        send=SendPoller(ReadOnlyHttpClient(settings.diddisend_base_url, client)),
        food=FoodPoller(ReadOnlyHttpClient(settings.diddifoood_base_url, client)),
    )
