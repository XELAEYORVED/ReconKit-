"""Network mapping module (RIPEstat).

Maps the autonomous system around a target IP/domain: ASN details, announced
prefixes and BGP neighbours (upstreams / downstreams). Uses the public RIPEstat
Data API — keyless and passive. (BGPView, the previous source, shut down.)
"""

from __future__ import annotations

from typing import Any

import dns.asyncresolver

from ..models import TargetType
from ..utils.validators import is_ip
from .base import BaseModule, ModuleResult, make_client

RIPESTAT = "https://stat.ripe.net/data/{call}/data.json?resource={resource}&sourceapp=reconkit"


class NetworkMapModule(BaseModule):
    name = "network_map"
    description = "ASN details, announced prefixes and BGP neighbours via RIPEstat."
    rate_limit = 1.0
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

    async def _stat(self, client, call: str, resource: str) -> dict[str, Any]:
        body = await self._get_json(
            client, RIPESTAT.format(call=call, resource=resource), source="ripestat"
        )
        return body.get("data", {}) if isinstance(body, dict) else {}

    async def run(self, target: str) -> ModuleResult:
        ip = await self._resolve(target)
        if not ip:
            return self.failed(target, "Could not resolve target to an IP")

        async with make_client(timeout=30.0) as client:
            try:
                info = await self._stat(client, "network-info", ip)
            except Exception as exc:
                return self.failed(target, f"RIPEstat lookup failed: {exc}")

            asns = info.get("asns") or []
            asn_num = int(asns[0]) if asns else None
            asn_detail: dict[str, Any] = {"asn": asn_num}
            prefixes: list[dict[str, Any]] = []
            peers: dict[str, list] = {"upstreams": [], "downstreams": [], "ixs": []}

            if asn_num:
                resource = f"AS{asn_num}"
                # Each call is optional: a partial map beats no map.
                try:
                    ov = await self._stat(client, "as-overview", resource)
                    holder = ov.get("holder") or ""
                    name, _, desc = holder.partition(" - ")
                    asn_detail.update({
                        "name": name or None,
                        "description": desc or holder or None,
                        "rir": (ov.get("block") or {}).get("desc"),
                        "announced": ov.get("announced"),
                    })
                except Exception:
                    pass
                try:
                    loc = await self._stat(client, "rir-stats-country", resource)
                    located = loc.get("located_resources") or []
                    if located:
                        asn_detail["country"] = located[0].get("location")
                except Exception:
                    pass
                try:
                    ann = await self._stat(client, "announced-prefixes", resource)
                    prefixes = [{"prefix": p.get("prefix"), "name": asn_detail.get("name"),
                                 "country": asn_detail.get("country")}
                                for p in ann.get("prefixes", [])]
                except Exception:
                    pass
                try:
                    nb = await self._stat(client, "asn-neighbours", resource)
                    neighbours = sorted(nb.get("neighbours", []),
                                        key=lambda n: n.get("power", 0), reverse=True)
                    peers["upstreams"] = [{"asn": n.get("asn"), "name": None}
                                          for n in neighbours if n.get("type") == "left"][:30]
                    peers["downstreams"] = [{"asn": n.get("asn"), "name": None}
                                            for n in neighbours if n.get("type") == "right"][:30]
                    peers["counts"] = nb.get("neighbour_counts", {})
                except Exception:
                    pass

        data = {
            "ip": ip,
            "ip_prefix": info.get("prefix"),
            "asn": asn_detail,
            "prefixes": prefixes[:50],
            "prefix_count": len(prefixes),
            "peers": peers,
        }
        return self.ok(target, data, tags=["network", "bgp", "infrastructure"])
