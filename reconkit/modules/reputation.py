"""Reputation module (AbuseIPDB, VirusTotal, AlienVault OTX).

Aggregates reputation signals for an IP or domain from threat-intel providers.
Each provider is used only if its API key is configured; the module degrades
gracefully and reports which providers contributed.
"""

from __future__ import annotations

import dns.asyncresolver

from ..models import TargetType
from ..utils.validators import is_ip
from .base import BaseModule, ModuleResult, make_client


class ReputationModule(BaseModule):
    name = "reputation"
    description = "IP/domain reputation from AbuseIPDB, VirusTotal and AlienVault OTX."
    rate_limit = 1.0
    requires_api_key = False  # degrades per-provider
    supported_types = (TargetType.DOMAIN, TargetType.IP)
    category = "reputation"

    async def _resolve_ip(self, target: str) -> str | None:
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

    async def _abuseipdb(self, client, ip: str) -> dict | None:
        key = self.settings.abuseipdb_api_key
        if not key or not ip:
            return None
        try:
            res = await self._get_json(
                client,
                f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}&maxAgeInDays=90",
                source="abuseipdb",
                headers={"Key": key, "Accept": "application/json"},
            )
        except Exception:
            return None
        d = res.get("data", {})
        return {
            "abuse_confidence": d.get("abuseConfidenceScore"),
            "total_reports": d.get("totalReports"),
            "country": d.get("countryCode"),
            "is_tor": d.get("isTor"),
            "usage_type": d.get("usageType"),
        }

    async def _virustotal(self, client, target: str, is_ip_target: bool) -> dict | None:
        key = self.settings.virustotal_api_key
        if not key:
            return None
        kind = "ip_addresses" if is_ip_target else "domains"
        try:
            res = await self._get_json(
                client,
                f"https://www.virustotal.com/api/v3/{kind}/{target}",
                source="virustotal",
                headers={"x-apikey": key},
            )
        except Exception:
            return None
        stats = res.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        return {
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless": stats.get("harmless", 0),
            "undetected": stats.get("undetected", 0),
        }

    async def _otx(self, client, target: str, is_ip_target: bool) -> dict | None:
        key = self.settings.otx_api_key
        if not key:
            return None
        kind = "IPv4" if is_ip_target else "domain"
        try:
            res = await self._get_json(
                client,
                f"https://otx.alienvault.com/api/v1/indicators/{kind}/{target}/general",
                source="otx",
                headers={"X-OTX-API-KEY": key},
            )
        except Exception:
            return None
        return {
            "pulse_count": res.get("pulse_info", {}).get("count", 0),
            "reputation": res.get("reputation"),
        }

    async def run(self, target: str) -> ModuleResult:
        is_ip_target = is_ip(target)
        ip = target if is_ip_target else await self._resolve_ip(target)

        providers_available = any([
            self.settings.abuseipdb_api_key,
            self.settings.virustotal_api_key,
            self.settings.otx_api_key,
        ])
        if not providers_available:
            return self.skipped(
                target,
                "No reputation API keys configured (AbuseIPDB / VirusTotal / OTX).",
            )

        async with make_client(timeout=20.0) as client:
            abuse = await self._abuseipdb(client, ip or "")
            vt = await self._virustotal(client, target, is_ip_target)
            otx = await self._otx(client, target, is_ip_target)

        malicious_signals = 0
        if abuse and (abuse.get("abuse_confidence") or 0) > 25:
            malicious_signals += 1
        if vt and vt.get("malicious", 0) > 0:
            malicious_signals += 1
        if otx and otx.get("pulse_count", 0) > 0:
            malicious_signals += 1

        data = {
            "ip": ip,
            "abuseipdb": abuse,
            "virustotal": vt,
            "otx": otx,
            "malicious_signals": malicious_signals,
            "providers_used": [n for n, v in
                               [("abuseipdb", abuse), ("virustotal", vt), ("otx", otx)] if v],
        }
        return self.ok(target, data, tags=["reputation", "threat-intel"])
