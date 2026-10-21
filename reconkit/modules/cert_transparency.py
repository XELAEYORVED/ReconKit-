"""Certificate Transparency module (crt.sh).

Queries the public crt.sh CT log index for all certificates issued for a
domain. Passive: read-only queries to a public log aggregator.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client


class CertTransparencyModule(BaseModule):
    name = "cert_transparency"
    description = "All issued certificates, SANs, issuers and validity windows via crt.sh."
    rate_limit = 2.0
    supported_types = (TargetType.DOMAIN,)
    category = "infrastructure"

    async def run(self, target: str) -> ModuleResult:
        url = f"https://crt.sh/?q=%25.{target}&output=json"
        async with make_client(timeout=30.0) as client:
            try:
                entries = await self._get_json(client, url, source="crt.sh")
            except Exception as exc:
                return self.failed(target, f"crt.sh query failed: {exc}")

        if not isinstance(entries, list):
            return self.failed(target, "Unexpected crt.sh response")

        issuers: Counter[str] = Counter()
        names: set[str] = set()
        certs: list[dict[str, Any]] = []
        seen_serials: set[str] = set()
        for e in entries:
            issuer = (e.get("issuer_name") or "").split("O=")[-1].split(",")[0] or e.get("issuer_name")
            issuers[issuer] += 1
            for nm in (e.get("name_value") or "").splitlines():
                nm = nm.strip().lstrip("*.").lower()
                if nm.endswith(target):
                    names.add(nm)
            serial = e.get("serial_number")
            if serial and serial not in seen_serials:
                seen_serials.add(serial)
                certs.append({
                    "id": e.get("id"),
                    "issuer": issuer,
                    "common_name": e.get("common_name"),
                    "not_before": e.get("not_before"),
                    "not_after": e.get("not_after"),
                    "serial": serial,
                })

        data = {
            "total_certificates": len(entries),
            "unique_certificates": len(certs),
            "san_hostnames": sorted(names),
            "san_count": len(names),
            "issuers": dict(issuers.most_common(15)),
            "certificates": certs[:200],
        }
        return self.ok(target, data, tags=["certificates", "infrastructure"])
