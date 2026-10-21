"""Shodan reconnaissance module.

With a Shodan API key, uses the host API for full service/banner/vuln data.
Without a key, falls back to Shodan's keyless InternetDB endpoint
(internetdb.shodan.io) which returns open ports, hostnames and known CVEs.

This module reads Shodan's *existing, pre-collected* data. ReconKit never
scans the target itself — it only reads what Shodan already published.
"""

from __future__ import annotations

import dns.asyncresolver

from ..models import TargetType
from ..utils.validators import is_ip
from .base import BaseModule, ModuleResult, make_client


class ShodanModule(BaseModule):
    name = "shodan"
    description = "Open ports, services, banners and known CVEs from Shodan (InternetDB keyless)."
    rate_limit = 1.0
    requires_api_key = False  # degrades to keyless InternetDB
    api_service = "shodan"
    supported_types = (TargetType.DOMAIN, TargetType.IP)
    category = "technology"

    async def _resolve(self, target: str) -> str | None:
        if is_ip(target):
            return target
        r = dns.asyncresolver.Resolver()
        r.nameservers = ["1.1.1.1", "8.8.8.8"]
        r.lifetime = 5.0
        try:
            ans = await r.resolve(target, "A")
            return ans[0].to_text()
        except Exception:
            return None

    async def run(self, target: str) -> ModuleResult:
        ip = await self._resolve(target)
        if not ip:
            return self.failed(target, "Could not resolve target to an IP")

        key = self.settings.shodan_api_key
        async with make_client(timeout=20.0) as client:
            if key:
                try:
                    data = await self._get_json(
                        client, f"https://api.shodan.io/shodan/host/{ip}?key={key}",
                        source="shodan",
                    )
                    services = [
                        {
                            "port": s.get("port"),
                            "transport": s.get("transport"),
                            "product": s.get("product"),
                            "version": s.get("version"),
                            "banner": (s.get("data") or "")[:300],
                        }
                        for s in data.get("data", [])
                    ]
                    return self.ok(target, {
                        "ip": ip,
                        "source": "shodan-api",
                        "ports": data.get("ports", []),
                        "hostnames": data.get("hostnames", []),
                        "org": data.get("org"),
                        "os": data.get("os"),
                        "vulns": list(data.get("vulns", []) or []),
                        "services": services,
                    }, tags=["shodan", "technology", "exposure"])
                except Exception:
                    pass  # fall through to keyless

            # Keyless InternetDB.
            try:
                data = await self._get_json(
                    client, f"https://internetdb.shodan.io/{ip}", source="internetdb"
                )
            except Exception as exc:
                return self.failed(target, f"Shodan/InternetDB lookup failed: {exc}")

        return self.ok(target, {
            "ip": ip,
            "source": "internetdb-keyless",
            "ports": data.get("ports", []),
            "hostnames": data.get("hostnames", []),
            "cpes": data.get("cpes", []),
            "vulns": data.get("vulns", []),
            "tags": data.get("tags", []),
        }, confidence=0.85, tags=["shodan", "technology", "exposure"])
