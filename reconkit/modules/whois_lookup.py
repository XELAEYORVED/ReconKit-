"""WHOIS / RDAP lookup module.

Uses RDAP (structured, modern) as the primary source and falls back to the
classic ``python-whois`` parser. Purely passive: a single registry query.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client


def _iso(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_iso(v) for v in value]
    return value


class WhoisModule(BaseModule):
    name = "whois"
    description = "Registrar, registration dates, contacts and name servers (RDAP + WHOIS)."
    rate_limit = 1.0
    supported_types = (TargetType.DOMAIN, TargetType.IP)
    category = "infrastructure"

    async def _rdap(self, target: str) -> dict[str, Any] | None:
        url = f"https://rdap.org/domain/{target}"
        async with make_client() as client:
            try:
                data = await self._get_json(client, url, source="rdap")
            except Exception:
                return None
        events = {e.get("eventAction"): e.get("eventDate") for e in data.get("events", [])}
        name_servers = [ns.get("ldhName") for ns in data.get("nameservers", []) if ns.get("ldhName")]
        registrar = None
        contacts: list[dict[str, Any]] = []
        for ent in data.get("entities", []):
            roles = ent.get("roles", [])
            vcard = ent.get("vcardArray")
            name = None
            if isinstance(vcard, list) and len(vcard) > 1:
                for item in vcard[1]:
                    if item and item[0] == "fn":
                        name = item[3]
            if "registrar" in roles and name:
                registrar = name
            contacts.append({"roles": roles, "name": name, "handle": ent.get("handle")})
        return {
            "source": "rdap",
            "registrar": registrar,
            "status": data.get("status", []),
            "name_servers": name_servers,
            "created": events.get("registration"),
            "updated": events.get("last changed") or events.get("last update of RDAP database"),
            "expires": events.get("expiration"),
            "contacts": contacts,
        }

    async def _whois(self, target: str) -> dict[str, Any] | None:
        try:
            import whois  # python-whois, synchronous
        except Exception:
            return None

        def _lookup() -> dict[str, Any]:
            w = whois.whois(target)
            return {
                "source": "whois",
                "registrar": _iso(w.get("registrar")),
                "status": _iso(w.get("status")),
                "name_servers": _iso(w.get("name_servers")),
                "created": _iso(w.get("creation_date")),
                "updated": _iso(w.get("updated_date")),
                "expires": _iso(w.get("expiration_date")),
                "emails": _iso(w.get("emails")),
                "org": _iso(w.get("org")),
                "country": _iso(w.get("country")),
            }

        try:
            return await asyncio.to_thread(_lookup)
        except Exception:
            return None

    async def run(self, target: str) -> ModuleResult:
        rdap = await self._rdap(target)
        whois_data = await self._whois(target)
        if not rdap and not whois_data:
            return self.failed(target, "No WHOIS/RDAP data available")
        data: dict[str, Any] = {}
        # Prefer RDAP, enrich with whois fields.
        if rdap:
            data.update({k: v for k, v in rdap.items() if v})
        if whois_data:
            for k, v in whois_data.items():
                data.setdefault(k, v)
            if whois_data.get("emails"):
                data["emails"] = whois_data["emails"]
        confidence = 1.0 if rdap else 0.75
        return self.ok(target, data, confidence=confidence, tags=["whois", "infrastructure"])
