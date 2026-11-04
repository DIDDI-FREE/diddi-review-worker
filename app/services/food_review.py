from app.adapters.diddifood import DiddiFoodAdapter
from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.observation.pollers import FoodPoller, PollContext
from app.orchestration.food_workflow import FoodRestaurantWorkflow
from app.orchestration.reactive import ReactiveCoordinator
from app.persistence.event_ledger import EventLedger

# DiddiFood order statuses -> restaurant workflow step tokens. Statuses from
# "ready" onward are terminal for the restaurant leg and intentionally skipped.
_FOOD_STATUS = {
    "placed": "PENDING",
    "preparing": "PREPARING",
}

# Preparation time the runner (acting as the restaurant) commits to on accept.
_PREP_MINUTES = 10


class FoodReviewService:
    """Reviewer is the customer; the runner plays the restaurant.

    It accepts the order (with a prep time) and marks it ready. The courier leg
    of a Food order is carried by DiddiSend (origin_module=diddifood) and is
    handled separately.
    """

    def __init__(self, *, registry: ReviewAccountRegistry, tokens: ReviewTokenCache, poller: FoodPoller, adapter: DiddiFoodAdapter, ledger: EventLedger) -> None:
        self.registry, self.tokens, self.poller, self.adapter, self.ledger = registry, tokens, poller, adapter, ledger
        self.coordinator = ReactiveCoordinator(registry.bindings())

    async def run_once(self) -> int:
        handled = 0
        for account in self.registry.accounts:
            if not account.enabled or account.product != "diddifood" or account.tested_role != "customer":
                continue
            customer_token = await self.tokens.get(account.reviewer_user_id)
            events = await self.poller.customer_orders(PollContext(account.reviewer_user_id, customer_token))
            for event in events:
                if not self.coordinator.react(event):
                    continue
                key = self.coordinator.event_key(event)
                claimed = self.ledger.claim(key)
                if hasattr(claimed, "__await__"):
                    claimed = await claimed
                if not claimed:
                    continue
                detail = await self.adapter.get_order(event.resource_id, token=customer_token)
                order = detail.get("order", detail)
                mapped = _FOOD_STATUS.get(str(order.get("status", "")).lower())
                restaurant_id = order.get("restaurant_id")
                if mapped is None or not restaurant_id:
                    continue
                restaurant_token = await self.tokens.get(account.counter_user_id)
                workflow = FoodRestaurantWorkflow(self.adapter)
                await workflow.advance(str(restaurant_id), event.resource_id, token=restaurant_token, server_status=mapped, prep_minutes=_PREP_MINUTES, key_prefix=key)
                handled += 1
        return handled
