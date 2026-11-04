from app.adapters.diddisend import DiddiSendAdapter
from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.config.settings import Settings
from app.observation.pollers import PollContext, SendPoller
from app.orchestration.professional_triggers import ProfessionalTriggerRunner
from app.persistence.event_ledger import EventLedger


class SendProfessionalService:
    """Reviewer is the courier; when they go online the runner plays the client
    and creates exactly one delivery nearby (task 3)."""

    def __init__(self, *, registry: ReviewAccountRegistry, tokens: ReviewTokenCache, poller: SendPoller, adapter: DiddiSendAdapter, settings: Settings, ledger: EventLedger) -> None:
        self.registry, self.tokens, self.poller, self.adapter, self.settings, self.ledger = registry, tokens, poller, adapter, settings, ledger
        self.runner = ProfessionalTriggerRunner()
        self._primed: set[str] = set()

    def _coords(self) -> tuple[dict, dict]:
        s = self.settings
        pickup = {"lat": s.request_pickup_lat, "lng": s.request_pickup_lng, "address": s.request_pickup_address}
        dropoff = {"lat": s.request_dropoff_lat, "lng": s.request_dropoff_lng, "address": s.request_dropoff_address}
        return pickup, dropoff

    async def run_once(self) -> int:
        created = 0
        for account in self.registry.accounts:
            if not account.enabled or account.product != "diddisend" or account.tested_role != "courier":
                continue
            reviewer_token = await self.tokens.get(account.reviewer_user_id)
            online = await self.poller.courier_online(PollContext(account.reviewer_user_id, reviewer_token))
            key = f"diddisend:{account.reviewer_user_id}"
            if key not in self._primed:
                # Seed the baseline without acting so a courier already online at
                # startup is not treated as a fresh transition (task 3).
                self.runner.availability.transition_to_available(key, online)
                self._primed.add(key)
                continue
            pickup, dropoff = self._coords()

            async def _create(account=account, pickup=pickup, dropoff=dropoff):
                claim_key = f"diddisend:courier:{account.reviewer_user_id}:online"
                claimed = self.ledger.claim(claim_key)
                if hasattr(claimed, "__await__"):
                    claimed = await claimed
                if not claimed:
                    return None
                client_token = await self.tokens.get(account.counter_user_id)
                return await self.adapter.create_delivery(token=client_token, sender_user_id=account.counter_user_id, pickup=pickup, dropoff=dropoff, key=claim_key)

            result = await self.runner.on_availability(product="diddisend", user_id=account.reviewer_user_id, available=online, create_request=_create)
            if result is not None:
                created += 1
        return created
