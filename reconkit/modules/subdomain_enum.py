"""Passive subdomain enumeration.

Aggregates subdomains from multiple passive sources (crt.sh CT logs, the
HackerTarget passive API, and RapidDNS), de-duplicates, and optionally
confirms which currently resolve. No brute forcing or active probing.
"""

from __future__ import annotations

import asyncio
import re

import dns.asyncresolver

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client

_SUB_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9-]+)+")


class SubdomainEnumModule(BaseModule):
    name = "subdomains"
    description = "Discover subdomains from crt.sh, HackerTarget and RapidDNS (passive)."
    rate_limit = 2.0
    supported_types = (TargetType.DOMAIN,)
    category = "infrastructure"

    async def _from_crtsh(self, client, target: str) -> set[str]:
        url = f"https://crt.sh/?q=%25.{target}&output=json"
        try:
            entries = await self._get_json(client, url, source="crt.sh")
        except Exception:
            return set()
        found: set[str] = set()
        for e in entries if isinstance(entries, list) else []:
            for nm in (e.get("name_value") or "").splitlines():
                nm = nm.strip().lstrip("*.").lower()
                if nm.endswith(target):
                    found.add(nm)
        return found

    async def _from_hackertarget(self, client, target: str) -> set[str]:
        url = f"https://api.hackertarget.com/hostsearch/?q={target}"
        try:
            text = await self._get_text(client, url, source="hackertarget")
        except Exception:
            return set()
        found: set[str] = set()
        for line in text.splitlines():
            host = line.split(",")[0].strip().lower()
            if host.endswith(target):
                found.add(host)
        return found

    async def _from_rapiddns(self, client, target: str) -> set[str]:
        url = f"https://rapiddns.io/subdomain/{target}?full=1"
        try:
            html = await self._get_text(client, url, source="rapiddns")
        except Exception:
            return set()
        found = {m.lower() for m in _SUB_RE.findall(html) if m.lower().endswith(target)}
        return found

    async def _resolves(self, resolver, name: str) -> tuple[str, list[str]]:
        try:
            ans = await resolver.resolve(name, "A")
            return name, [r.to_text() for r in ans]
        except Exception:
            return name, []

    async def run(self, target: str) -> ModuleResult:
        async with make_client(timeout=30.0) as client:
            sources = await asyncio.gather(
                self._from_crtsh(client, target),
                self._from_hackertarget(client, target),
                self._from_rapiddns(client, target),
                return_exceptions=True,
            )
        names: set[str] = set()
        source_counts = {}
        for label, result in zip(["crtsh", "hackertarget", "rapiddns"], sources):
            if isinstance(result, set):
                source_counts[label] = len(result)
                names |= result
        names.discard(target)

        if not names:
            return self.failed(target, "No subdomains discovered from passive sources")

        # Confirm resolution for up to 100 candidates (concurrent, light).
        resolver = dns.asyncresolver.Resolver()
        resolver.nameservers = ["1.1.1.1", "8.8.8.8"]
        resolver.lifetime = 5.0
        candidates = sorted(names)
        sem = asyncio.Semaphore(20)

        async def _guarded(n):
            async with sem:
                return await self._resolves(resolver, n)

        resolved = await asyncio.gather(*[_guarded(n) for n in candidates[:150]])
        live = {n: ips for n, ips in resolved if ips}

        data = {
            "subdomains": candidates,
            "count": len(candidates),
            "live": live,
            "live_count": len(live),
            "source_counts": source_counts,
        }
        return self.ok(target, data, tags=["subdomains", "infrastructure"])
