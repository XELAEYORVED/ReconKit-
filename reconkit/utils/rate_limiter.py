"""Per-source async rate limiting with exponential backoff.

Each named source (e.g. "crt.sh", "shodan") gets its own limiter that enforces
a minimum interval between requests. Limiters are process-global and shared
across modules so concurrent scans do not hammer the same API.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections import defaultdict


class RateLimiter:
    """Minimum-interval limiter for a single source."""

    def __init__(self, min_interval: float = 1.0) -> None:
        self.min_interval = max(0.0, min_interval)
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._last + self.min_interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()


class RateLimiterRegistry:
    """Holds one limiter per source name."""

    def __init__(self, default_interval: float = 1.0) -> None:
        self.default_interval = default_interval
        self._limiters: dict[str, RateLimiter] = {}
        self._overrides: dict[str, float] = defaultdict(lambda: default_interval)

    def configure(self, overrides: dict[str, float]) -> None:
        self._overrides.update(overrides or {})

    def get(self, source: str) -> RateLimiter:
        if source not in self._limiters:
            interval = self._overrides.get(source, self.default_interval)
            self._limiters[source] = RateLimiter(interval)
        return self._limiters[source]

    async def acquire(self, source: str) -> None:
        await self.get(source).acquire()


async def with_backoff(
    coro_factory,
    *,
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_on=(Exception,),
):
    """Run ``coro_factory()`` with exponential backoff + jitter on failure.

    ``coro_factory`` is a zero-arg callable returning a fresh awaitable each
    attempt (so it can be retried). Re-raises the last exception if all
    attempts fail.
    """
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return await coro_factory()
        except retry_on as exc:  # type: ignore[misc]
            last_exc = exc
            if attempt >= retries:
                break
            delay = min(max_delay, base_delay * (2 ** attempt))
            delay += random.uniform(0, delay * 0.25)
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc


# Process-global registry (configured from settings at engine startup).
registry = RateLimiterRegistry()
