from app.adapters.diddigo import DiddiGoAdapter
from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.config.settings import Settings
from app.observation.pollers import IdentityPoller, PollContext
from app.orchestration.professional_triggers import ProfessionalTriggerRunner
from app.persistence.event_ledger import EventLedger


class GoProfessionalService:
    """Reviewer is the driver; when they go online the runner plays the passenger
    and requests exactly one ride (task 3).

    DiddiGo exposes no readable driver online state, so the transition is observed
    through the driver's own DiddiFreeID capability projection (GET /pro/me). That
    projection is push-based and carries a freshness marker, so detection depends
    on DiddiGo having projected the status.
    """

    def __init__(self, *, registry: ReviewAccountRegistry, tokens: ReviewTokenCache, poller: IdentityPoller, adapter: DiddiGoAdapter, settings: Settings, ledger: EventLedger) -> None:
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
            if not account.enabled or account.product != "diddigo" or account.tested_role != "driver":
                continue
            reviewer_token = await self.tokens.get(account.reviewer_user_id)
            online = await self.poller.driver_online(PollContext(account.reviewer_user_id, reviewer_token))
            key = f"diddigo:{account.reviewer_user_id}"
            if key not in self._primed:
                # Seed baseline so a driver already online at startup is not a transition.
                self.runner.availability.transition_to_available(key, online)
                self._primed.add(key)
                continue
            pickup, dropoff = self._coords()

            async def _create(account=account, pickup=pickup, dropoff=dropoff):
                claim_key = f"diddigo:driver:{account.reviewer_user_id}:online"
                claimed = self.ledger.claim(claim_key)
                if hasattr(claimed, "__await__"):
                    claimed = await claimed
                if not claimed:
                    return None
                client_token = await self.tokens.get(account.counter_user_id)
                quote = await self.adapter.estimate_ride(token=client_token, pickup=pickup, dropoff=dropoff, key=f"{claim_key}:estimate")
                quote_id = quote.payload.get("quote_id")
                if not quote_id:
                    return None
                return await self.adapter.create_ride(token=client_token, quote_id=str(quote_id), key=f"{claim_key}:create")

            result = await self.runner.on_availability(product="diddigo", user_id=account.reviewer_user_id, available=online, create_request=_create)
            if result is not None:
                created += 1
        return created
