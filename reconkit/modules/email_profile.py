"""Email profile module.

Keyless, passive look at an email address: what kind of provider hosts it
(free webmail, disposable, or a company domain), whether the domain can
receive mail (MX), its anti-spoofing policies (SPF / DMARC), and whether a
public Gravatar profile is attached to the address.
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any

import dns.asyncresolver

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client

FREE_PROVIDERS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "hotmail.fr", "live.com",
    "live.fr", "msn.com", "yahoo.com", "yahoo.fr", "ymail.com", "icloud.com", "me.com",
    "mac.com", "aol.com", "proton.me", "protonmail.com", "pm.me", "gmx.com", "gmx.fr",
    "gmx.de", "web.de", "mail.com", "zoho.com", "yandex.com", "yandex.ru", "free.fr",
    "orange.fr", "wanadoo.fr", "laposte.net", "sfr.fr", "neuf.fr", "bbox.fr", "skynet.be",
    "telenet.be", "tutanota.com", "tuta.io", "fastmail.com", "hey.com", "qq.com", "163.com",
}
DISPOSABLE_PROVIDERS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com", "temp-mail.org",
    "yopmail.com", "yopmail.fr", "trashmail.com", "sharklasers.com", "getnada.com",
    "dispostable.com", "maildrop.cc", "throwawaymail.com", "mohmal.com", "emailondeck.com",
}


class EmailProfileModule(BaseModule):
    name = "email_profile"
    description = "Email provider type, MX / SPF / DMARC of its domain, and public Gravatar profile."
    rate_limit = 0.5
    supported_types = (TargetType.EMAIL,)
    category = "identity"

    def _resolver(self) -> dns.asyncresolver.Resolver:
        r = dns.asyncresolver.Resolver()
        r.nameservers = ["1.1.1.1", "8.8.8.8"]
        r.lifetime = 6.0
        return r

    async def _txt(self, resolver, name: str, rtype: str = "TXT") -> list[str]:
        try:
            ans = await resolver.resolve(name, rtype)
        except Exception:
            return []
        return [r.to_text().strip('"') for r in ans]

    async def _gravatar(self, email: str) -> dict[str, Any]:
        digest = hashlib.md5(email.strip().lower().encode()).hexdigest()
        out: dict[str, Any] = {"exists": False}
        async with make_client(timeout=15.0) as client:
            try:
                await self._rate_limited("gravatar")
                resp = await client.get(f"https://en.gravatar.com/{digest}.json")
            except Exception:
                return out
            if resp.status_code != 200:
                return out
            try:
                entry = (resp.json().get("entry") or [{}])[0]
            except Exception:
                return out
        out.update({
            "exists": True,
            "profile_url": entry.get("profileUrl"),
            "username": entry.get("preferredUsername"),
            "display_name": entry.get("displayName"),
            "avatar_url": entry.get("thumbnailUrl"),
            "location": entry.get("currentLocation"),
            "accounts": [{"site": a.get("shortname") or a.get("domain"), "url": a.get("url")}
                         for a in entry.get("accounts", [])][:20],
        })
        return out

    async def run(self, target: str) -> ModuleResult:
        email = target.strip()
        local, _, domain = email.rpartition("@")
        domain = domain.lower()
        if not local or not domain:
            return self.failed(target, "Not a valid email address")

        resolver = self._resolver()
        mx, txt, dmarc, gravatar = await asyncio.gather(
            self._txt(resolver, domain, "MX"),
            self._txt(resolver, domain),
            self._txt(resolver, f"_dmarc.{domain}"),
            self._gravatar(email),
        )
        spf = [t for t in txt if t.lower().startswith("v=spf1")]
        dmarc = [d for d in dmarc if "dmarc" in d.lower()]
        dmarc_policy = None
        if dmarc:
            for part in dmarc[0].split(";"):
                k, _, v = part.strip().partition("=")
                if k.lower() == "p":
                    dmarc_policy = v.strip().lower()

        if domain in DISPOSABLE_PROVIDERS:
            provider = "disposable"
        elif domain in FREE_PROVIDERS:
            provider = "free_webmail"
        else:
            provider = "custom_domain"

        data = {
            "email": email,
            "local_part": local,
            "domain": domain,
            "provider_type": provider,
            "can_receive_mail": bool(mx),
            "mx": sorted(mx),
            "spf": spf,
            "dmarc": dmarc,
            "dmarc_policy": dmarc_policy,
            "gravatar": gravatar,
        }
        return self.ok(target, data, tags=["identity", "email"])
