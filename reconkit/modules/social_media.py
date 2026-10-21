"""Social media profile discovery (username OSINT).

Checks for the existence of a public profile page for a given username across
common platforms, Namechk/Sherlock style. Passive: it performs a single
unauthenticated GET per platform to the public profile URL and inspects the
HTTP status / known "not found" markers — no login, no scraping of private
data.
"""

from __future__ import annotations

import asyncio

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client

# platform -> (profile url template, absence marker or None -> use 404)
PLATFORMS = {
    "GitHub": ("https://github.com/{u}", None),
    "GitLab": ("https://gitlab.com/{u}", None),
    "Twitter/X": ("https://nitter.net/{u}", "User not found"),
    "Instagram": ("https://www.instagram.com/{u}/", None),
    "Reddit": ("https://www.reddit.com/user/{u}", "nobody on Reddit"),
    "TikTok": ("https://www.tiktok.com/@{u}", None),
    "Twitch": ("https://m.twitch.tv/{u}", None),
    "Medium": ("https://medium.com/@{u}", None),
    "Keybase": ("https://keybase.io/{u}", None),
    "Pinterest": ("https://www.pinterest.com/{u}/", None),
    "Telegram": ("https://t.me/{u}", "tgme_page_additional"),
    "YouTube": ("https://www.youtube.com/@{u}", None),
    "HackerNews": ("https://news.ycombinator.com/user?id={u}", "No such user"),
    "Dev.to": ("https://dev.to/{u}", None),
    "Replit": ("https://replit.com/@{u}", None),
}


class SocialMediaModule(BaseModule):
    name = "social"
    description = "Discover public profiles for a username across major platforms."
    rate_limit = 0.3
    supported_types = (TargetType.USERNAME,)
    category = "identity"

    async def _check(self, client, platform, template, marker, username):
        url = template.format(u=username)
        try:
            await self._rate_limited("social")
            resp = await client.get(url)
        except Exception:
            return platform, {"url": url, "exists": None, "status": "error"}
        exists = resp.status_code == 200
        if exists and marker and marker.lower() in resp.text.lower():
            exists = False
        return platform, {
            "url": url,
            "exists": exists,
            "status_code": resp.status_code,
        }

    async def run(self, target: str) -> ModuleResult:
        async with make_client(timeout=12.0) as client:
            sem = asyncio.Semaphore(8)

            async def guarded(p, t, m):
                async with sem:
                    return await self._check(client, p, t, m, target)

            results = await asyncio.gather(
                *[guarded(p, t, m) for p, (t, m) in PLATFORMS.items()]
            )
        profiles = dict(results)
        found = {p: d for p, d in profiles.items() if d.get("exists")}
        data = {
            "username": target,
            "found": found,
            "found_count": len(found),
            "checked": len(profiles),
            "all": profiles,
        }
        return self.ok(target, data, confidence=0.7, tags=["identity", "social"])
