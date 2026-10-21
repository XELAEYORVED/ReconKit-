"""Google dorking module (Programmable Search / CSE API).

Runs a curated set of passive Google dorks scoped to the target domain to
surface exposed files, directory listings and sensitive pages. Requires a
Google CSE API key + engine id; skips gracefully otherwise.
"""

from __future__ import annotations

import asyncio

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client

DORKS = [
    'site:{d} ext:sql | ext:env | ext:log | ext:bak',
    'site:{d} intitle:"index of"',
    'site:{d} ext:xml | ext:conf | ext:cnf | ext:ini',
    'site:{d} inurl:admin | inurl:login | inurl:dashboard',
    'site:{d} ext:pdf | ext:doc | ext:docx | ext:xls',
    'site:{d} intext:"password" | intext:"api_key"',
]


class GoogleDorkingModule(BaseModule):
    name = "google_dork"
    description = "Automated passive Google dorks via the Programmable Search (CSE) API."
    rate_limit = 1.0
    requires_api_key = True
    api_service = "google_cse"
    supported_types = (TargetType.DOMAIN,)
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
        findings: list[dict] = []
        async with make_client(timeout=20.0) as client:
            for dork in DORKS:
                q = dork.format(d=target)
                url = (
                    "https://www.googleapis.com/customsearch/v1"
                    f"?key={key}&cx={cx}&q={q}&num=10"
                )
                try:
                    res = await self._get_json(client, url, source="google_cse")
                except Exception:
                    await asyncio.sleep(1)
                    continue
                for item in res.get("items", []):
                    findings.append({
                        "dork": dork,
                        "title": item.get("title"),
                        "url": item.get("link"),
                        "snippet": item.get("snippet"),
                    })

        data = {
            "findings": findings,
            "finding_count": len(findings),
            "dorks_run": len(DORKS),
        }
        return self.ok(target, data, tags=["exposure", "dorks"])
