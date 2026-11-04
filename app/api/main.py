from fastapi import Depends, FastAPI, Header, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import Settings, get_settings
from app.observability import correlation_middleware
from app.orchestration import Orchestrator
from app.persistence import InMemoryRunRepository
from app.scenarios import RunRequest

app = FastAPI(title="diddi-review-runner", version="0.1.0")
app.add_middleware(BaseHTTPMiddleware, dispatch=correlation_middleware)
repository = InMemoryRunRepository()
orchestrator = Orchestrator(repository)


def require_service_auth(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> None:
    if authorization != f"Bearer {settings.runner_service_token}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid service credentials")


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/v1/runs", status_code=202, dependencies=[Depends(require_service_auth)])
async def create_run(request: RunRequest) -> dict:
    try:
        return (await orchestrator.create(request)).__dict__
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/v1/runs/{run_id}", dependencies=[Depends(require_service_auth)])
async def get_run(run_id: str) -> dict:
    record = repository.get(run_id)
    if record is None:
        raise HTTPException(404, "run not found")
    return record.__dict__


@app.post("/v1/runs/{run_id}/cancel", dependencies=[Depends(require_service_auth)])
async def cancel_run(run_id: str) -> dict:
    try:
        return orchestrator.cancel(run_id).__dict__
    except KeyError as exc:
        raise HTTPException(404, "run not found") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/v1/runs/{run_id}/retry", dependencies=[Depends(require_service_auth)])
async def retry_run(run_id: str) -> dict:
    try:
        return orchestrator.retry(run_id).__dict__
    except KeyError as exc:
        raise HTTPException(404, "run not found") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
