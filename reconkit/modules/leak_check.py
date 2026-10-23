"""Data-leak / breach check module (Have I Been Pwned).

For an email target, queries HIBP's breach API (requires an HIBP API key).
Without a key the module reports which public breach data *would* be checked
and degrades gracefully. ReconKit only reports breach *metadata* (names,
dates, data classes) — never leaked credentials.
"""

from __future__ import annotations

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client


class LeakCheckModule(BaseModule):
    name = "leak_check"
    description = "Check an email against known data breaches (Have I Been Pwned)."
    rate_limit = 1.6  # HIBP requires >=1.5s between requests
    requires_api_key = True
    api_service = "hibp"  # HIBP_API_KEY
    supported_types = (TargetType.EMAIL,)
    category = "identity"

    def available(self) -> bool:
        return bool(self.settings.hibp_api_key)

    async def run(self, target: str) -> ModuleResult:
        key = self.settings.hibp_api_key
        if not key:
            return self.skipped(
                target, "HIBP_API_KEY not set — breach lookup requires a Have I Been Pwned key."
            )

        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{target}?truncateResponse=false"
        headers = {"hibp-api-key": key, "User-Agent": "ReconKit"}
        async with make_client(timeout=20.0) as client:
            try:
                await self._rate_limited("hibp")
                resp = await client.get(url, headers=headers)
            except Exception as exc:
                return self.failed(target, f"HIBP request failed: {exc}")

        if resp.status_code == 404:
            return self.ok(target, {"breached": False, "breaches": []},
                           tags=["identity", "breach"])
        if resp.status_code == 401:
            return self.failed(target, "HIBP key rejected (401)")
        if resp.status_code != 200:
            return self.failed(target, f"HIBP returned {resp.status_code}")

        breaches = resp.json()
        data = {
            "breached": bool(breaches),
            "breach_count": len(breaches),
            "breaches": [
                {
                    "name": b.get("Name"),
                    "domain": b.get("Domain"),
                    "breach_date": b.get("BreachDate"),
                    "pwn_count": b.get("PwnCount"),
                    "data_classes": b.get("DataClasses", []),
                    "verified": b.get("IsVerified"),
                }
                for b in breaches
            ],
        }
        return self.ok(target, data, tags=["identity", "breach", "exposure"])
