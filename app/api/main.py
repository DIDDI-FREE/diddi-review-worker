import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.adapters.diddifood import DiddiFoodAdapter
from app.adapters.diddigo import DiddiGoAdapter
from app.adapters.diddisend import DiddiSendAdapter
from app.bootstrap import build_runtime
from app.config.settings import Settings, get_settings
from app.observability import correlation_middleware
from app.orchestration import Orchestrator
from app.persistence import InMemoryRunRepository
from app.runtime import build_production_dependencies
from app.scenarios import RunRequest
from app.services.food_review import FoodReviewService
from app.services.go_review import GoReviewService
from app.services.send_review import SendReviewService

logger = logging.getLogger(__name__)

async def _reactive_loop(settings: Settings, stop: asyncio.Event) -> None:
    timeout = httpx.Timeout(settings.http_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        runtime = build_runtime(settings, client)
        production = build_production_dependencies(settings)
        go_service = GoReviewService(
            registry=runtime.registry,
            tokens=runtime.tokens,
            poller=runtime.go,
            adapter=DiddiGoAdapter("diddigo", settings.diddigo_base_url, client),
            ledger=production.events,
        )
        send_service = SendReviewService(
            registry=runtime.registry,
            tokens=runtime.tokens,
            poller=runtime.send,
            adapter=DiddiSendAdapter("diddisend", settings.diddisend_base_url, client),
            ledger=production.events,
        )
        food_service = FoodReviewService(
            registry=runtime.registry,
            tokens=runtime.tokens,
            poller=runtime.food,
            adapter=DiddiFoodAdapter("diddifood", settings.diddifood_base_url, client),
            ledger=production.events,
        )
        while not stop.is_set():
            try:
                await go_service.run_once()
            except (httpx.HTTPError, ValueError, RuntimeError) as exc:
                logger.warning("reactive Go poll failed; will retry", exc_info=exc)
            try:
                await send_service.run_once()
            except (httpx.HTTPError, ValueError, RuntimeError) as exc:
                logger.warning("reactive Send poll failed; will retry", exc_info=exc)
            try:
                await food_service.run_once()
            except (httpx.HTTPError, ValueError, RuntimeError) as exc:
                logger.warning("reactive Food poll failed; will retry", exc_info=exc)
            try:
                await asyncio.wait_for(stop.wait(), timeout=settings.reactive_poll_interval_seconds)
            except TimeoutError:
                pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    stop = asyncio.Event()
    task = asyncio.create_task(_reactive_loop(settings, stop)) if settings.reactive_enabled else None
    yield
    if task is not None:
        stop.set()
        await task


app = FastAPI(title="diddi-review-runner", version="0.1.0", lifespan=lifespan)
app.add_middleware(BaseHTTPMiddleware, dispatch=correlation_middleware)
repository = InMemoryRunRepository()
orchestrator = Orchestrator(repository)


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/v1/runs", status_code=202)
async def create_run(request: RunRequest) -> dict:
    try:
        return (await orchestrator.create(request)).__dict__
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/v1/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    record = repository.get(run_id)
    if record is None:
        raise HTTPException(404, "run not found")
    return record.__dict__


@app.post("/v1/runs/{run_id}/cancel")
async def cancel_run(run_id: str) -> dict:
    try:
        return orchestrator.cancel(run_id).__dict__
    except KeyError as exc:
        raise HTTPException(404, "run not found") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/v1/runs/{run_id}/retry")
async def retry_run(run_id: str) -> dict:
    try:
        return orchestrator.retry(run_id).__dict__
    except KeyError as exc:
        raise HTTPException(404, "run not found") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
