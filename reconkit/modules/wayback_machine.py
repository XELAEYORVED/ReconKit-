"""Wayback Machine module (Internet Archive CDX API).

Retrieves historical snapshots and archived URLs for a domain. Keyless and
fully passive (public archive index).
"""

from __future__ import annotations

import asyncio
from collections import Counter
from urllib.parse import urlparse

from ..models import TargetType
from ..utils.rate_limiter import with_backoff
from .base import BaseModule, ModuleResult, make_client

CDX_BUDGET = 60.0  # seconds for the full index before falling back


class WaybackModule(BaseModule):
    name = "wayback"
    description = "Historical snapshots and archived URLs from the Internet Archive CDX API."
    rate_limit = 1.5
    supported_types = (TargetType.DOMAIN,)
    category = "history"

    async def run(self, target: str) -> ModuleResult:
        url = (
            "https://web.archive.org/cdx/search/cdx"
            f"?url={target}/*&output=json&fl=timestamp,original,statuscode,mimetype"
            "&collapse=urlkey&limit=5000"
        )
        async with make_client(timeout=30.0) as client:
            try:
                # The CDX index is slow on big sites and often overloaded (503).
                # Retry within a fixed budget, then fall back to the light API.
                rows = await asyncio.wait_for(
                    with_backoff(lambda: self._get_json(client, url, source="wayback"),
                                 retries=1, base_delay=3.0),
                    timeout=CDX_BUDGET,
                )
            except (Exception, asyncio.TimeoutError) as exc:
                return await self._fallback(client, target, exc)

        if not isinstance(rows, list) or len(rows) < 2:
            return self.ok(target, {"snapshot_count": 0, "urls": []}, confidence=0.6,
                           tags=["history"])

        header, *data_rows = rows
        timestamps = [r[0] for r in data_rows if r and r[0].isdigit()]
        urls = [r[1] for r in data_rows if len(r) > 1]
        exts: Counter[str] = Counter()
        paths: set[str] = set()
        for u in urls:
            p = urlparse(u).path
            paths.add(p)
            if "." in p.rsplit("/", 1)[-1]:
                exts[p.rsplit(".", 1)[-1].lower()[:8]] += 1

        first = min(timestamps) if timestamps else None
        last = max(timestamps) if timestamps else None

        data = {
            "snapshot_count": len(data_rows),
            "first_capture": first,
            "last_capture": last,
            "unique_urls": len(set(urls)),
            "sample_urls": sorted(set(urls))[:300],
            "extensions": dict(exts.most_common(20)),
            "interesting": sorted(
                p for p in paths
                if any(k in p.lower() for k in
                       ("admin", "login", "config", "backup", ".sql", ".env", "api", ".git"))
            )[:100],
        }
        return self.ok(target, data, tags=["history", "wayback"])

    async def _fallback(self, client, target: str, exc: Exception) -> ModuleResult:
        """CDX unavailable: use the lightweight availability API for the latest snapshot."""
        try:
            body = await asyncio.wait_for(self._get_json(
                client, f"https://archive.org/wayback/available?url={target}", source="wayback"
            ), timeout=30.0)
        except (Exception, asyncio.TimeoutError):
            return self.failed(target, f"Wayback Machine unavailable, try again later ({exc or 'timeout'})")
        snap = (body.get("archived_snapshots") or {}).get("closest") or {}
        if not snap.get("available"):
            return self.ok(target, {"snapshot_count": 0, "urls": [],
                                    "note": "Full archive index unavailable; no snapshot found."},
                           confidence=0.4, tags=["history"])
        ts = snap.get("timestamp")
        return self.ok(target, {
            "snapshot_count": 1,
            "first_capture": None,
            "last_capture": ts,
            "latest_snapshot_url": snap.get("url"),
            "unique_urls": 0,
            "sample_urls": [],
            "extensions": {},
            "interesting": [],
            "note": "Full archive index was unavailable; showing the latest snapshot only.",
        }, confidence=0.5, tags=["history", "wayback"])
