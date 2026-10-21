"""Pytest fixtures: isolated temp DB, disabled cache, no API keys."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _env(tmp_path_factory):
    """Point ReconKit at a throwaway sqlite DB and disable caching/keys."""
    tmp = tmp_path_factory.mktemp("reconkit")
    db = tmp / "test.db"
    os.environ["RECONKIT_DATABASE_URL"] = f"sqlite+aiosqlite:///{db.as_posix()}"
    os.environ["RECONKIT_CACHE_BACKEND"] = "none"
    os.environ["RECONKIT_SECRET_KEY"] = "test-secret"
    os.environ["RECONKIT_REQUIRE_AUTH"] = "false"
    # Ensure no real keys leak into tests.
    for k in ("SHODAN_API_KEY", "VIRUSTOTAL_API_KEY", "HIBP_API_KEY",
              "GOOGLE_CSE_API_KEY", "HUNTER_API_KEY"):
        os.environ.pop(k, None)

    from reconkit.config import get_settings
    from reconkit.utils import cache

    get_settings.cache_clear()
    cache.reset_cache()
    _register_fake_module()
    yield


def _register_fake_module():
    """A deterministic offline module for hermetic engine/API tests."""
    from reconkit.models import TargetType
    from reconkit.modules.base import REGISTRY, BaseModule, ModuleResult

    if "fake" in REGISTRY:
        return

    class FakeModule(BaseModule):
        name = "fake"
        description = "Deterministic test module (no network)."
        supported_types = (TargetType.DOMAIN,)
        category = "infrastructure"

        async def run(self, target: str) -> ModuleResult:
            return self.ok(target, {"ipv4": ["1.2.3.4"], "hello": "world"},
                           tags=["infrastructure"])


@pytest.fixture
def anyio_backend():
    return "asyncio"
