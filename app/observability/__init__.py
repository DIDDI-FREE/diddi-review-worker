from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")


async def correlation_middleware(request: Request, call_next):
    value = request.headers.get("X-Correlation-ID") or str(uuid4())
    correlation_id.set(value)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = value
    return response

