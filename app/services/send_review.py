from datetime import UTC, datetime

from app.adapters.diddisend import DiddiSendAdapter
from app.auth.token_cache import ReviewTokenCache
from app.config.review_accounts import ReviewAccountRegistry
from app.observation.pollers import PollContext, SendPoller
from app.orchestration.reactive import ReactiveCoordinator
from app.orchestration.send_workflow import SendCourierWorkflow
from app.persistence.event_ledger import EventLedger

# Map DiddiSend's lowercase delivery statuses onto the workflow's step tokens.
# Terminal statuses (delivered/cancelled/failed) are intentionally absent: the
# service skips them so the runner never re-acts on a finished delivery.
_SEND_STATUS = {
    "created": "OFFERED",
    "awaiting_pickup": "OFFERED",
    "assigned": "ACCEPTED",
    "picked_up": "PICKED_UP",
}


class SendReviewService:
    """Reviewer is the sender; the runner plays the courier (accept + pickup).

    The final ``deliver`` step is PIN-gated and the courier cannot legitimately
    read that PIN, so the workflow stops at PICKED_UP and waits for the reviewer.
    """

    def __init__(self, *, registry: ReviewAccountRegistry, tokens: ReviewTokenCache, poller: SendPoller, adapter: DiddiSendAdapter, ledger: EventLedger) -> None:
        self.registry, self.tokens, self.poller, self.adapter, self.ledger = registry, tokens, poller, adapter, ledger
        self.coordinator = ReactiveCoordinator(registry.bindings())

    async def run_once(self) -> int:
        handled = 0
        for account in self.registry.accounts:
            if not account.enabled or account.product != "diddisend" or account.tested_role != "sender":
                continue
            sender_token = await self.tokens.get(account.reviewer_user_id)
            events = await self.poller.sender_deliveries(PollContext(account.reviewer_user_id, sender_token))
            for event in events:
                if not self.coordinator.react(event):
                    continue
                key = self.coordinator.event_key(event)
                claimed = self.ledger.claim(key)
                if hasattr(claimed, "__await__"):
                    claimed = await claimed
                if not claimed:
                    continue
                detail = await self.adapter.get_delivery(event.resource_id, token=sender_token)
                body = detail.get("delivery", detail)
                mapped = _SEND_STATUS.get(str(body.get("status", "")).lower())
                if mapped is None:
                    continue
                courier_token = await self.tokens.get(account.counter_user_id)
                pickup = body.get("pickup_location") or {}
                location = None
                if pickup.get("lat") is not None and pickup.get("lng") is not None:
                    location = {"lat": pickup["lat"], "lng": pickup["lng"]}
                now = datetime.now(UTC).isoformat()
                workflow = SendCourierWorkflow(self.adapter)
                await workflow.advance(event.resource_id, token=courier_token, server_status=mapped, location=location, recorded_at=now, delivery_pin=None, key_prefix=key)
                handled += 1
        return handled
