"""Pastebin monitoring module.

Searches public paste sites for mentions of the target via the Google CSE API
(scoped to pastebin.com, ghostbin, throwbin, etc.). Requires a Google CSE key;
skips gracefully otherwise. Read-only and passive.
"""

from __future__ import annotations

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client

PASTE_SITES = [
    "pastebin.com", "ghostbin.com", "throwbin.io", "controlc.com",
    "rentry.co", "paste.ee", "justpaste.it",
]


class PastebinMonitorModule(BaseModule):
    name = "pastebin"
    description = "Search public paste sites for mentions of the target (via Google CSE)."
    rate_limit = 1.0
    requires_api_key = True
    api_service = "google_cse"
    supported_types = (TargetType.DOMAIN, TargetType.EMAIL)
    category = "exposure"

    def available(self) -> bool:
        return bool(self.settings.google_cse_api_key and self.settings.google_cse_id)

    async def run(self, target: str) -> ModuleResult:
        if not self.available():
            return self.skipped(
                target, "GOOGLE_CSE_API_KEY / GOOGLE_CSE_ID not configured."
            )
        key = self.settings.google_cse_api_key
        cx = self.settings.google_cse_id
        sites = " OR ".join(f"site:{s}" for s in PASTE_SITES)
        q = f'"{target}" ({sites})'
        url = f"https://www.googleapis.com/customsearch/v1?key={key}&cx={cx}&q={q}&num=10"
        async with make_client(timeout=20.0) as client:
            try:
                res = await self._get_json(client, url, source="google_cse")
            except Exception as exc:
                return self.failed(target, f"Paste search failed: {exc}")

        hits = [
            {"title": i.get("title"), "url": i.get("link"), "snippet": i.get("snippet")}
            for i in res.get("items", [])
        ]
        data = {"hits": hits, "hit_count": len(hits), "sites_checked": PASTE_SITES}
        return self.ok(target, data, tags=["exposure", "pastebin"])
