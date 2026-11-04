from collections.abc import Awaitable, Callable



TERMINAL_CODES = {"ALREADY_RATED", "NOT_OWNER", "NOT_COMPLETED", "NOT_DELIVERED", "REVIEW_PRODUCTION_MISMATCH"}


async def bounded_retry(action: Callable[[], Awaitable[object]], *, attempts: int = 3) -> object:
    last_error: Exception | None = None
    for _ in range(max(1, attempts)):
        try:
            return await action()
        except Exception as exc:  # caller classifies terminal errors upstream
            if getattr(exc, "code", None) in TERMINAL_CODES:
                raise
            last_error = exc
    raise RuntimeError("bounded retry exhausted") from last_error
