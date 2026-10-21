"""Network mapping module (BGPView).

Maps the autonomous system around a target IP/domain: ASN details, announced
prefixes, upstream/downstream peers and IX presence. Keyless, passive.
"""

from __future__ import annotations

import dns.asyncresolver

from ..models import TargetType
from ..utils.validators import is_ip
from .base import BaseModule, ModuleResult, make_client


class NetworkMapModule(BaseModule):
    name = "network_map"
    description = "ASN details, announced prefixes and BGP peers via BGPView."
    rate_limit = 2.0
    supported_types = (TargetType.DOMAIN, TargetType.IP)
    category = "infrastructure"

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

        async with make_client(timeout=20.0) as client:
            try:
                ipinfo = await self._get_json(
                    client, f"https://api.bgpview.io/ip/{ip}", source="bgpview"
                )
            except Exception as exc:
                return self.failed(target, f"BGPView lookup failed: {exc}")

            prefixes = ipinfo.get("data", {}).get("prefixes", [])
            asn_num = None
            if prefixes:
                asn_num = prefixes[0].get("asn", {}).get("asn")

            asn_detail = {}
            peers = {"upstreams": [], "downstreams": [], "ixs": []}
            if asn_num:
                try:
                    detail = await self._get_json(
                        client, f"https://api.bgpview.io/asn/{asn_num}", source="bgpview"
                    )
                    d = detail.get("data", {})
                    asn_detail = {
                        "asn": asn_num,
                        "name": d.get("name"),
                        "description": d.get("description_short"),
                        "country": d.get("country_code"),
                        "website": d.get("website"),
                        "rir": d.get("rir_allocation", {}).get("rir_name"),
                    }
                    peer = await self._get_json(
                        client, f"https://api.bgpview.io/asn/{asn_num}/upstreams", source="bgpview"
                    )
                    ups = peer.get("data", {}).get("ipv4_upstreams", [])
                    peers["upstreams"] = [
                        {"asn": u.get("asn"), "name": u.get("name")} for u in ups[:30]
                    ]
                except Exception:
                    pass

        data = {
            "ip": ip,
            "asn": asn_detail or {"asn": asn_num},
            "prefixes": [
                {"prefix": p.get("prefix"), "name": p.get("name"),
                 "country": p.get("country_code")}
                for p in prefixes[:50]
            ],
            "prefix_count": len(prefixes),
            "peers": peers,
        }
        return self.ok(target, data, tags=["network", "bgp", "infrastructure"])
