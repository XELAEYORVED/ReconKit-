"""Email harvesting module.

Collects email addresses associated with a domain from passive sources:
Hunter.io (if a key is set), WHOIS/RDAP registrant emails, and a crawl-free
scrape of the domain homepage. Also infers the likely corporate email format.
"""

from __future__ import annotations

import re

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


class EmailHarvestModule(BaseModule):
    name = "email"
    description = "Harvest emails and infer the corporate address format (Hunter.io + homepage)."
    rate_limit = 1.0
    requires_api_key = False
    api_service = "hunter"
    supported_types = (TargetType.DOMAIN,)
    category = "identity"

    async def _hunter(self, client, domain: str) -> dict:
        key = self.settings.hunter_api_key
        if not key:
            return {}
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={key}"
        try:
            res = await self._get_json(client, url, source="hunter")
        except Exception:
            return {}
        d = res.get("data", {})
        return {
            "pattern": d.get("pattern"),
            "organization": d.get("organization"),
            "emails": [
                {"value": e.get("value"), "type": e.get("type"),
                 "confidence": e.get("confidence")}
                for e in d.get("emails", [])
            ],
        }

    async def _homepage_emails(self, client, domain: str) -> set[str]:
        found: set[str] = set()
        for scheme in ("https", "http"):
            try:
                await self._rate_limited("email")
                resp = await client.get(f"{scheme}://{domain}")
                found |= {
                    m.lower() for m in _EMAIL_RE.findall(resp.text)
                    if m.lower().endswith(domain)
                }
                break
            except Exception:
                continue
        return found

    async def run(self, target: str) -> ModuleResult:
        async with make_client(timeout=20.0) as client:
            hunter = await self._hunter(client, target)
            homepage = await self._homepage_emails(client, target)

        emails = set(homepage)
        for e in hunter.get("emails", []):
            if e.get("value"):
                emails.add(e["value"].lower())

        pattern = hunter.get("pattern")
        data = {
            "emails": sorted(emails),
            "email_count": len(emails),
            "pattern": pattern,
            "organization": hunter.get("organization"),
            "hunter_enabled": bool(self.settings.hunter_api_key),
            "sources": {
                "homepage": sorted(homepage),
                "hunter": len(hunter.get("emails", [])),
            },
        }
        conf = 0.9 if self.settings.hunter_api_key else 0.6
        return self.ok(target, data, confidence=conf, tags=["identity", "email"])
