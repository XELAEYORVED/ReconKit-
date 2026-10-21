"""GitHub reconnaissance module.

Searches public GitHub for mentions of a domain and for common secret-leak
dork patterns scoped to the domain. Works unauthenticated (low rate limit);
a ``GITHUB_TOKEN`` raises the limit and enables code search.

Passive: read-only queries to GitHub's public search API. ReconKit reports
*where* potential secrets may be exposed; it does not exfiltrate contents.
"""

from __future__ import annotations

import asyncio

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client

SECRET_DORKS = [
    'password', 'api_key', 'apikey', 'secret', 'token',
    'BEGIN RSA PRIVATE KEY', 'aws_access_key_id', 'AKIA',
]


class GithubReconModule(BaseModule):
    name = "github"
    description = "Find public GitHub mentions and potential secret-leak hits for a domain."
    rate_limit = 6.0  # unauthenticated search is heavily throttled
    requires_api_key = False
    api_service = "github"
    supported_types = (TargetType.DOMAIN,)
    category = "identity"

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/vnd.github+json"}
        if self.settings.github_token:
            h["Authorization"] = f"Bearer {self.settings.github_token}"
        return h

    async def _search(self, client, endpoint: str, q: str) -> dict:
        url = f"https://api.github.com/search/{endpoint}?q={q}&per_page=10"
        return await self._get_json(client, url, source="github", headers=self._headers())

    async def run(self, target: str) -> ModuleResult:
        authed = bool(self.settings.github_token)
        async with make_client(timeout=25.0) as client:
            repos = {}
            try:
                repos = await self._search(client, "repositories", target)
            except Exception:
                repos = {}

            code_hits = []
            if authed:
                for dork in SECRET_DORKS:
                    try:
                        res = await self._search(client, "code", f'"{target}" {dork}')
                        for item in res.get("items", [])[:5]:
                            code_hits.append({
                                "dork": dork,
                                "repo": item.get("repository", {}).get("full_name"),
                                "path": item.get("path"),
                                "url": item.get("html_url"),
                            })
                    except Exception:
                        await asyncio.sleep(1)
                        continue

        repo_items = [
            {"full_name": r.get("full_name"), "url": r.get("html_url"),
             "stars": r.get("stargazers_count"), "description": r.get("description")}
            for r in (repos.get("items", []) if isinstance(repos, dict) else [])
        ]
        data = {
            "authenticated": authed,
            "repo_mentions": repo_items,
            "repo_mention_count": repos.get("total_count", 0) if isinstance(repos, dict) else 0,
            "potential_secret_hits": code_hits,
            "secret_hit_count": len(code_hits),
            "note": None if authed else "Set GITHUB_TOKEN to enable code/secret search.",
        }
        conf = 0.9 if authed else 0.5
        return self.ok(target, data, confidence=conf, tags=["github", "identity", "exposure"])
