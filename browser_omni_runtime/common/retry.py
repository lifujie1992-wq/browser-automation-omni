from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar('T')


async def async_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    factor: float = 2.0,
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    last_error: BaseException | None = None
    delay = base_delay
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except retry_exceptions as exc:
            last_error = exc
            if attempt >= attempts:
                break
            await asyncio.sleep(delay)
            delay *= factor
    assert last_error is not None
    raise last_error
