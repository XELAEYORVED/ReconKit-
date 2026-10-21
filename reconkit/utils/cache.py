"""Result caching for ReconKit.

Supports three backends: ``disk`` (JSON files under the cache dir), ``redis``
(if the optional redis extra is installed), and ``none``. The cache is keyed
by module name + target and has a configurable TTL to avoid redundant
external requests.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from ..config import get_settings


def _key(namespace: str, target: str) -> str:
    raw = f"{namespace}:{target}".encode()
    return hashlib.sha256(raw).hexdigest()[:40]


class BaseCache:
    async def get(self, namespace: str, target: str) -> Any | None:  # pragma: no cover
        return None

    async def set(self, namespace: str, target: str, value: Any) -> None:  # pragma: no cover
        return None


class NullCache(BaseCache):
    pass


class DiskCache(BaseCache):
    def __init__(self, directory: str, ttl: int) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl

    def _path(self, namespace: str, target: str) -> Path:
        return self.dir / f"{_key(namespace, target)}.json"

    async def get(self, namespace: str, target: str) -> Any | None:
        path = self._path(namespace, target)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if self.ttl and time.time() - payload.get("_ts", 0) > self.ttl:
            return None
        return payload.get("value")

    async def set(self, namespace: str, target: str, value: Any) -> None:
        path = self._path(namespace, target)
        try:
            path.write_text(
                json.dumps({"_ts": time.time(), "value": value}, default=str),
                encoding="utf-8",
            )
        except OSError:
            pass


class RedisCache(BaseCache):
    def __init__(self, url: str, ttl: int) -> None:
        import redis.asyncio as redis  # lazy import; optional dependency

        self._redis = redis.from_url(url, decode_responses=True)
        self.ttl = ttl

    async def get(self, namespace: str, target: str) -> Any | None:
        raw = await self._redis.get(_key(namespace, target))
        return json.loads(raw) if raw else None

    async def set(self, namespace: str, target: str, value: Any) -> None:
        await self._redis.set(
            _key(namespace, target), json.dumps(value, default=str), ex=self.ttl or None
        )


_cache: BaseCache | None = None


def get_cache() -> BaseCache:
    global _cache
    if _cache is not None:
        return _cache
    settings = get_settings()
    backend = settings.cache_backend.lower()
    if backend == "redis":
        try:
            _cache = RedisCache(settings.redis_url, settings.cache_ttl)
        except Exception:
            _cache = DiskCache(settings.cache_dir, settings.cache_ttl)
    elif backend == "none":
        _cache = NullCache()
    else:
        _cache = DiskCache(settings.cache_dir, settings.cache_ttl)
    return _cache


def reset_cache() -> None:
    """Testing helper: drop the cached backend singleton."""
    global _cache
    _cache = None
