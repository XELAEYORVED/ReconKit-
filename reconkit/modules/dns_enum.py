"""DNS enumeration module.

Resolves the full set of common record types plus derived security records
(SPF, DMARC). Uses dnspython's async resolver. Passive: standard public DNS
queries only, no zone transfers or brute forcing.
"""

from __future__ import annotations

import asyncio
from typing import Any

import dns.asyncresolver
import dns.resolver

from ..models import TargetType
from .base import BaseModule, ModuleResult

RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME", "SRV", "CAA"]


class DnsEnumModule(BaseModule):
    name = "dns"
    description = "Resolve A/AAAA/MX/NS/TXT/SOA/CNAME/SRV/CAA plus SPF & DMARC policies."
    rate_limit = 0.2
    supported_types = (TargetType.DOMAIN,)
    category = "infrastructure"

    def _resolver(self) -> dns.asyncresolver.Resolver:
        r = dns.asyncresolver.Resolver()
        r.lifetime = 8.0
        r.timeout = 4.0
        # Public resolvers for reliable passive resolution.
        r.nameservers = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
        return r

    async def _query(self, resolver, name: str, rtype: str) -> list[str]:
        try:
            answer = await resolver.resolve(name, rtype)
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            return []
        except Exception:
            return []
        out = []
        for r in answer:
            out.append(r.to_text().strip('"') if rtype == "TXT" else r.to_text())
        return out

    async def run(self, target: str) -> ModuleResult:
        resolver = self._resolver()
        records: dict[str, list[str]] = {}

        results = await asyncio.gather(
            *[self._query(resolver, target, rt) for rt in RECORD_TYPES]
        )
        for rt, vals in zip(RECORD_TYPES, results):
            if vals:
                records[rt] = vals

        # Derived security records.
        txt = records.get("TXT", [])
        spf = [t for t in txt if t.lower().startswith("v=spf1")]
        dmarc = await self._query(resolver, f"_dmarc.{target}", "TXT")
        dkim_hint = await self._query(resolver, f"default._domainkey.{target}", "TXT")

        if not records and not dmarc:
            return self.failed(target, "No DNS records resolved")

        data: dict[str, Any] = {
            "records": records,
            "spf": spf,
            "dmarc": [d for d in dmarc if "dmarc" in d.lower()],
            "dkim_default": bool(dkim_hint),
            "has_mx": "MX" in records,
            "ipv4": records.get("A", []),
            "ipv6": records.get("AAAA", []),
        }
        return self.ok(target, data, tags=["dns", "infrastructure"])
