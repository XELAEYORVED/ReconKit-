"""IP geolocation and ASN module.

Resolves a domain to its A record first (if needed), then enriches the IP with
geolocation (ip-api.com, keyless) and ASN/organisation data (ipinfo.io if a
token is set, else ip-api). Passive public lookups only.
"""

from __future__ import annotations

import dns.asyncresolver

from ..models import TargetType
from ..utils.validators import is_ip
from .base import BaseModule, ModuleResult, make_client


class IpGeolocationModule(BaseModule):
    name = "ip_geo"
    description = "IP geolocation, ASN, network range and hosting organisation."
    rate_limit = 1.5
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

        async with make_client(timeout=15.0) as client:
            geo = {}
            try:
                fields = "status,message,country,countryCode,regionName,city,lat,lon,timezone,isp,org,as,asname,reverse,query"
                geo = await self._get_json(
                    client, f"http://ip-api.com/json/{ip}?fields={fields}", source="ip-api"
                )
            except Exception as exc:
                return self.failed(target, f"Geolocation lookup failed: {exc}")

            ipinfo = {}
            if self.settings.ipinfo_token:
                try:
                    ipinfo = await self._get_json(
                        client,
                        f"https://ipinfo.io/{ip}?token={self.settings.ipinfo_token}",
                        source="ipinfo",
                    )
                except Exception:
                    ipinfo = {}

        if geo.get("status") == "fail":
            return self.failed(target, geo.get("message", "ip-api failure"))

        asn = (geo.get("as") or "").split(" ")[0] if geo.get("as") else ipinfo.get("org", "").split(" ")[0]
        data = {
            "ip": ip,
            "country": geo.get("country"),
            "country_code": geo.get("countryCode"),
            "region": geo.get("regionName"),
            "city": geo.get("city"),
            "lat": geo.get("lat"),
            "lon": geo.get("lon"),
            "timezone": geo.get("timezone"),
            "isp": geo.get("isp"),
            "org": geo.get("org") or ipinfo.get("org"),
            "asn": asn,
            "as_name": geo.get("asname"),
            "reverse_dns": geo.get("reverse") or ipinfo.get("hostname"),
            "ipinfo": ipinfo or None,
        }
        return self.ok(target, data, tags=["geolocation", "infrastructure"])
