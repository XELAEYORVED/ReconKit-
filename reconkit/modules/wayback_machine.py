"""Wayback Machine module (Internet Archive CDX API).

Retrieves historical snapshots and archived URLs for a domain. Keyless and
fully passive (public archive index).
"""

from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client


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
        async with make_client(timeout=40.0) as client:
            try:
                rows = await self._get_json(client, url, source="wayback")
            except Exception as exc:
                return self.failed(target, f"Wayback query failed: {exc}")

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
