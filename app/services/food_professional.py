from app.adapters.diddifood import DiddiFoodAdapter
from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.config.settings import Settings
from app.observation.pollers import FoodPoller, PollContext
from app.orchestration.professional_triggers import ProfessionalTriggerRunner
from app.persistence.event_ledger import EventLedger


class FoodProfessionalService:
    """Reviewer is the restaurant; when it opens (status -> active) the runner
    plays the customer and places exactly one order at that restaurant (task 3)."""

    def __init__(self, *, registry: ReviewAccountRegistry, tokens: ReviewTokenCache, poller: FoodPoller, adapter: DiddiFoodAdapter, settings: Settings, ledger: EventLedger) -> None:
        self.registry, self.tokens, self.poller, self.adapter, self.settings, self.ledger = registry, tokens, poller, adapter, settings, ledger
        self.runner = ProfessionalTriggerRunner()
        self._primed: set[str] = set()

    def _dropoff(self) -> dict:
        s = self.settings
        return {"lat": s.request_dropoff_lat, "lng": s.request_dropoff_lng, "address": s.request_dropoff_address}

    async def run_once(self) -> int:
        created = 0
        for account in self.registry.accounts:
            if not account.enabled or account.product != "diddifood" or account.tested_role != "restaurant":
                continue
            reviewer_token = await self.tokens.get(account.reviewer_user_id)
            restaurant_id, active = await self.poller.my_restaurant(PollContext(account.reviewer_user_id, reviewer_token))
            if restaurant_id is None:
                continue
            key = f"diddifood:{account.reviewer_user_id}"
            if key not in self._primed:
                # Seed baseline so a restaurant already open at startup is not a transition.
                self.runner.availability.transition_to_available(key, active)
                self._primed.add(key)
                continue
            dropoff = self._dropoff()

            async def _create(account=account, restaurant_id=restaurant_id, dropoff=dropoff):
                claim_key = f"diddifood:restaurant:{account.reviewer_user_id}:online"
                claimed = self.ledger.claim(claim_key)
                if hasattr(claimed, "__await__"):
                    claimed = await claimed
                if not claimed:
                    return None
                client_token = await self.tokens.get(account.counter_user_id)
                menu = await self.adapter.get_menu(restaurant_id, token=client_token)
                dishes = menu.get("items", []) if isinstance(menu, dict) else []
                if not dishes:
                    return None
                items = [{"dish_id": str(dishes[0].get("id")), "quantity": 1}]
                return await self.adapter.place_order(restaurant_id, token=client_token, items=items, dropoff=dropoff, key=claim_key)

            result = await self.runner.on_availability(product="diddifood", user_id=account.reviewer_user_id, available=active, create_request=_create)
            if result is not None:
                created += 1
        return created
