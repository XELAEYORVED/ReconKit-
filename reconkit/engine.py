"""Asyncio orchestration engine for ReconKit.

Validates and type-detects a target, selects the relevant modules, runs them
concurrently under a semaphore and per-source rate limits, streams progress
events to an optional callback (used by the WebSocket layer), enriches the
combined results, computes the threat score, and persists everything.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from .config import get_settings
from .database import session_scope
from .models import Result, Scan, ScanStatus, TargetType
from .modules import get_registry
from .modules.base import BaseModule, ModuleResult
from .utils import enrichment
from .utils.rate_limiter import registry as rate_registry
from .utils.validators import detect_target_type, validate

ProgressCallback = Callable[[dict[str, Any]], Awaitable[None]]

# Which modules make sense per target type.
TYPE_MODULES: dict[TargetType, list[str]] = {
    TargetType.DOMAIN: [
        "whois", "dns", "subdomains", "cert_transparency", "tech", "headers",
        "wayback", "email", "metadata", "google_dork", "ip_geo", "reputation",
        "shodan", "github", "pastebin", "network_map",
    ],
    TargetType.IP: ["whois", "ip_geo", "reputation", "shodan", "network_map"],
    TargetType.EMAIL: ["email_profile", "leak_check", "pastebin"],
    TargetType.USERNAME: ["social"],
}


class ReconEngine:
    """Orchestrates passive recon modules."""

    def __init__(self, progress_cb: ProgressCallback | None = None) -> None:
        self.settings = get_settings()
        self.progress_cb = progress_cb
        rate_registry.default_interval = 1.0
        if self.settings.rate_limits:
            rate_registry.configure(self.settings.rate_limits)

    async def _emit(self, event: dict[str, Any]) -> None:
        if self.progress_cb:
            with contextlib.suppress(Exception):
                await self.progress_cb(event)

    def select_modules(self, target_type: TargetType,
                       requested: list[str] | None) -> list[BaseModule]:
        registry = get_registry()
        if requested:
            names = requested
        else:
            names = TYPE_MODULES.get(target_type, [])
        selected: list[BaseModule] = []
        for name in names:
            cls = registry.get(name)
            if not cls:
                continue
            mod = cls()
            if not mod.supports(target_type):
                continue
            selected.append(mod)
        return selected

    async def _run_one(self, module: BaseModule, target: str,
                       sem: asyncio.Semaphore, timeout: int,
                       total: int, counter: dict) -> ModuleResult:
        async with sem:
            await self._emit({"event": "module_start", "module": module.name})
            try:
                if not module.available():
                    result = module.skipped(target, "Module unavailable (missing API key)")
                else:
                    result = await asyncio.wait_for(
                        module.cached_run(target), timeout=timeout
                    )
            except asyncio.TimeoutError:
                result = module.failed(target, f"Timed out after {timeout}s")
            except Exception as exc:  # defensive: one module must never break others
                result = module.failed(target, f"{type(exc).__name__}: {exc}")

            counter["done"] += 1
            progress = counter["done"] / total if total else 1.0
            event_name = {
                "ok": "module_complete",
                "error": "module_error",
                "skipped": "module_complete",
            }.get(result.status, "module_complete")
            await self._emit({
                "event": event_name,
                "module": module.name,
                "status": result.status,
                "progress": round(progress, 3),
                "data": result.data if result.status == "ok" else {"error": result.error},
            })
            return result

    async def run_scan(
        self,
        target: str,
        modules: list[str] | None = None,
        *,
        target_type: TargetType | None = None,
        max_concurrency: int | None = None,
        timeout: int | None = None,
        scan_id: str | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Run a full passive scan and return a result dict."""
        tt = target_type or detect_target_type(target)
        validate(target, tt if tt != TargetType.UNKNOWN else None)

        max_concurrency = max_concurrency or self.settings.max_concurrency
        timeout = timeout or self.settings.default_timeout
        selected = self.select_modules(tt, modules)
        if not selected:
            raise ValueError(f"No applicable modules for target type '{tt.value}'")

        await self._emit({
            "event": "scan_start",
            "target": target,
            "target_type": tt.value,
            "modules": [m.name for m in selected],
        })

        sem = asyncio.Semaphore(max_concurrency)
        counter = {"done": 0}
        total = len(selected)
        results = await asyncio.gather(
            *[self._run_one(m, target, sem, timeout, total, counter) for m in selected]
        )

        score, factors = enrichment.compute_threat_score(results)
        graph = enrichment.build_relation_graph(target, results)
        summary = enrichment.build_summary(target, results, score, factors)
        summary["graph_node_count"] = len(graph["nodes"])

        payload = {
            "scan_id": scan_id,
            "target": target,
            "target_type": tt.value,
            "threat_score": score,
            "summary": summary,
            "graph": graph,
            "results": [r.to_dict() for r in results],
        }

        if persist:
            payload["scan_id"] = await self._persist(
                scan_id, target, tt, score, summary, graph, results, modules
            )

        await self._emit({
            "event": "scan_complete",
            "scan_id": payload["scan_id"],
            "threat_score": score,
            "progress": 1.0,
            "summary": summary,
        })
        return payload

    async def _persist(self, scan_id, target, tt, score, summary, graph, results, modules) -> str:
        async with session_scope() as session:
            scan: Scan | None = None
            if scan_id:
                scan = (await session.execute(
                    select(Scan).where(Scan.id == scan_id)
                )).scalar_one_or_none()
            if scan is None:
                scan = Scan(target=target, target_type=tt,
                            config={"modules": modules or "auto"})
                session.add(scan)
                await session.flush()
            scan.target_type = tt
            scan.status = ScanStatus.COMPLETED
            scan.threat_score = score
            summary = {**summary, "graph": graph}
            scan.summary = summary
            scan.completed_at = datetime.now(timezone.utc)
            for r in results:
                session.add(Result(
                    scan_id=scan.id, module_name=r.module_name, status=r.status,
                    data=r.data, confidence=r.confidence, tags=r.tags, error=r.error,
                ))
            return scan.id
