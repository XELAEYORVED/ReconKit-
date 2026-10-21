"""Abstract base class and registry for recon modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar

import httpx

from ..config import get_settings
from ..models import TargetType
from ..utils import validators
from ..utils.cache import get_cache
from ..utils.rate_limiter import registry as rate_registry
from ..utils.rate_limiter import with_backoff

USER_AGENT = "ReconKit/0.1 (+passive-osint; responsible use only)"


@dataclass
class ModuleResult:
    """Normalized output of a module run."""

    module_name: str
    target: str
    data: dict[str, Any] = field(default_factory=dict)
    raw: Any = None
    confidence: float = 1.0  # 0-1, reliability of the result
    tags: list[str] = field(default_factory=list)
    status: str = "ok"  # ok | error | skipped
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_name": self.module_name,
            "target": self.target,
            "data": self.data,
            "confidence": self.confidence,
            "tags": self.tags,
            "status": self.status,
            "error": self.error,
        }


# Global registry populated automatically by __init_subclass__.
REGISTRY: dict[str, type["BaseModule"]] = {}


class BaseModule(ABC):
    """Abstract base for all passive recon modules.

    Subclasses MUST keep ``passive_only = True``. The base class enforces this
    at registration time and refuses to register an active module.
    """

    name: ClassVar[str] = "base"
    description: ClassVar[str] = ""
    passive_only: ClassVar[bool] = True  # MUST remain True
    rate_limit: ClassVar[float] = 1.0  # seconds between requests to this source
    requires_api_key: ClassVar[bool] = False
    api_service: ClassVar[str | None] = None  # settings attr prefix, e.g. "shodan"
    # Which target types this module supports.
    supported_types: ClassVar[tuple[TargetType, ...]] = (TargetType.DOMAIN,)
    # Result categories for the UI graph / tabs.
    category: ClassVar[str] = "infrastructure"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "passive_only", False):
            raise TypeError(
                f"Module {cls.__name__} is not passive_only; ReconKit refuses "
                "to register active-recon modules."
            )
        if cls.name and cls.name != "base":
            REGISTRY[cls.name] = cls

    def __init__(self) -> None:
        self.settings = get_settings()
        # Register this module's rate limit under its source name.
        rate_registry.configure({self.name: self.rate_limit})

    # --- capability checks -------------------------------------------------
    def has_api_key(self) -> bool:
        if not self.api_service:
            return True
        return self.settings.has_key(self.api_service)

    def available(self) -> bool:
        """Whether the module can run given current configuration."""
        if self.requires_api_key:
            return self.has_api_key()
        return True

    def supports(self, target_type: TargetType) -> bool:
        return target_type in self.supported_types

    # --- helpers for subclasses -------------------------------------------
    async def _rate_limited(self, source: str | None = None) -> None:
        await rate_registry.acquire(source or self.name)

    async def _get_json(
        self, client: httpx.AsyncClient, url: str, *, source: str | None = None, **kwargs: Any
    ) -> Any:
        async def _do() -> Any:
            await self._rate_limited(source)
            resp = await client.get(url, **kwargs)
            resp.raise_for_status()
            return resp.json()

        return await with_backoff(_do, retries=2, base_delay=self.rate_limit or 1.0)

    async def _get_text(
        self, client: httpx.AsyncClient, url: str, *, source: str | None = None, **kwargs: Any
    ) -> str:
        async def _do() -> str:
            await self._rate_limited(source)
            resp = await client.get(url, **kwargs)
            resp.raise_for_status()
            return resp.text

        return await with_backoff(_do, retries=2, base_delay=self.rate_limit or 1.0)

    async def cached_run(self, target: str) -> ModuleResult:
        """Run with transparent caching keyed by module+target."""
        cache = get_cache()
        cached = await cache.get(self.name, target)
        if cached is not None:
            return ModuleResult(
                module_name=self.name,
                target=target,
                data=cached.get("data", {}),
                confidence=cached.get("confidence", 1.0),
                tags=cached.get("tags", []),
                status=cached.get("status", "ok"),
                error=cached.get("error"),
            )
        result = await self.run(target)
        if result.status == "ok":
            await cache.set(
                self.name,
                target,
                {
                    "data": result.data,
                    "confidence": result.confidence,
                    "tags": result.tags,
                    "status": result.status,
                    "error": result.error,
                },
            )
        return result

    def ok(self, target: str, data: dict[str, Any], *, confidence: float = 1.0,
           tags: list[str] | None = None) -> ModuleResult:
        return ModuleResult(
            module_name=self.name,
            target=target,
            data=data,
            confidence=confidence,
            tags=tags or [self.category],
            status="ok",
        )

    def skipped(self, target: str, reason: str) -> ModuleResult:
        return ModuleResult(
            module_name=self.name, target=target, data={"reason": reason},
            status="skipped", error=reason, tags=[self.category],
        )

    def failed(self, target: str, error: str) -> ModuleResult:
        return ModuleResult(
            module_name=self.name, target=target, data={}, status="error",
            error=error, confidence=0.0, tags=[self.category],
        )

    # --- interface ---------------------------------------------------------
    @abstractmethod
    async def run(self, target: str) -> ModuleResult:
        """Perform the passive lookup and return a ModuleResult."""

    def validate_target(self, target: str) -> bool:
        """Default validation using detected type against supported types."""
        try:
            detected = validators.detect_target_type(target)
        except ValueError:
            return False
        return detected in self.supported_types


def get_registry() -> dict[str, type[BaseModule]]:
    return dict(REGISTRY)


def get_module(name: str) -> BaseModule:
    if name not in REGISTRY:
        raise KeyError(f"Unknown module: {name}")
    return REGISTRY[name]()


def make_client(timeout: float = 20.0, **kwargs: Any) -> httpx.AsyncClient:
    """Factory for a configured async HTTP client used by modules."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9"}
    headers.update(kwargs.pop("headers", {}))
    return httpx.AsyncClient(
        timeout=timeout,
        headers=headers,
        follow_redirects=kwargs.pop("follow_redirects", True),
        **kwargs,
    )
