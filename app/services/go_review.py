from datetime import UTC, datetime

from app.adapters.diddigo import DiddiGoAdapter
from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.observation.pollers import GoPoller, PollContext
from app.orchestration.go_workflow import GoDriverWorkflow
from app.orchestration.reactive import ReactiveCoordinator
from app.persistence.event_ledger import EventLedger


class GoReviewService:
    def __init__(self, *, registry: ReviewAccountRegistry, tokens: ReviewTokenCache, poller: GoPoller, adapter: DiddiGoAdapter, ledger: EventLedger) -> None:
        self.registry, self.tokens, self.poller, self.adapter, self.ledger = registry, tokens, poller, adapter, ledger
        self.coordinator = ReactiveCoordinator(registry.bindings())

    async def run_once(self) -> int:
        handled = 0
        for account in self.registry.accounts:
            if not account.enabled or account.product != "diddigo" or account.tested_role != "passenger":
                continue
            passenger_token = await self.tokens.get(account.reviewer_user_id)
            events = await self.poller.rides(PollContext(account.reviewer_user_id, passenger_token), role="passenger")
            for event in events:
                if not self.coordinator.react(event):
                    continue
                key = self.coordinator.event_key(event)
                claimed = self.ledger.claim(key)
                if hasattr(claimed, "__await__"):
                    claimed = await claimed
                if not claimed:
                    continue
                detail = await self.adapter.get_ride(event.resource_id, token=passenger_token)
                driver_token = await self.tokens.get(account.counter_user_id)
                status = str(detail.get("status", "")).upper()
                pickup = detail.get("pickup") or {}
                dropoff = detail.get("dropoff") or {}
                now = datetime.now(UTC).isoformat()
                workflow = GoDriverWorkflow(self.adapter)
                if status in {"ACCEPTED", "ARRIVED", "IN_PROGRESS"}:
                    point = pickup if status == "ACCEPTED" else dropoff
                    if point.get("lat") is not None and point.get("lng") is not None:
                        await self.adapter.push_locations(event.resource_id, token=driver_token, samples=[{"lat": point["lat"], "lng": point["lng"], "recorded_at": now, "source": "driver"}], key=f"{key}:location:{status}")
                code = (detail.get("start_authorization") or {}).get("code")
                await workflow.advance(event.resource_id, token=driver_token, server_status=status, start_code=code, key_prefix=key)
                handled += 1
        return handled
