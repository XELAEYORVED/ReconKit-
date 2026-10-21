"""Technology detection module.

Fingerprints CMS, frameworks, CDN, analytics and server software from
response headers, cookies and HTML markers. A compact, offline ruleset (no
external Wappalyzer dependency) keyed on common signatures. Passive: one GET.
"""

from __future__ import annotations

import re

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client

# category -> list of (tech_name, kind, pattern)
# kind: "header:<name>", "cookie", "html", "generator", "script"
FINGERPRINTS = [
    ("WordPress", "cms", "html", r"wp-content|wp-includes|/wp-json"),
    ("Drupal", "cms", "header:x-generator", r"Drupal"),
    ("Joomla", "cms", "html", r"/media/jui/|Joomla!"),
    ("Ghost", "cms", "html", r"ghost-url|content=\"Ghost"),
    ("Shopify", "ecommerce", "html", r"cdn\.shopify\.com|Shopify\.theme"),
    ("Magento", "ecommerce", "cookie", r"X-Magento|mage-"),
    ("React", "framework", "html", r"data-reactroot|__REACT_DEVTOOLS|react(?:-dom)?\."),
    ("Vue.js", "framework", "html", r"data-v-[0-9a-f]{8}|__vue__|vue(?:\.min)?\.js"),
    ("Angular", "framework", "html", r"ng-version|ng-app|angular(?:\.min)?\.js"),
    ("Next.js", "framework", "html", r"/_next/|__NEXT_DATA__"),
    ("Nuxt", "framework", "html", r"__NUXT__|/_nuxt/"),
    ("Svelte", "framework", "html", r"svelte-[0-9a-z]+"),
    ("Laravel", "framework", "cookie", r"laravel_session|XSRF-TOKEN"),
    ("Django", "framework", "cookie", r"csrftoken|sessionid"),
    ("Express", "framework", "header:x-powered-by", r"Express"),
    ("ASP.NET", "framework", "header:x-powered-by", r"ASP\.NET"),
    ("PHP", "language", "header:x-powered-by", r"PHP"),
    ("Cloudflare", "cdn", "header:server", r"cloudflare"),
    ("Cloudflare", "cdn", "header:cf-ray", r".+"),
    ("Fastly", "cdn", "header:x-served-by", r"cache-|fastly"),
    ("Akamai", "cdn", "header:x-akamai-transformed", r".+"),
    ("Amazon CloudFront", "cdn", "header:x-amz-cf-id", r".+"),
    ("Nginx", "server", "header:server", r"nginx"),
    ("Apache", "server", "header:server", r"Apache"),
    ("Microsoft IIS", "server", "header:server", r"IIS|Microsoft-HTTPAPI"),
    ("LiteSpeed", "server", "header:server", r"LiteSpeed"),
    ("Google Analytics", "analytics", "html", r"google-analytics\.com|gtag\(|UA-\d+|G-[A-Z0-9]+"),
    ("Google Tag Manager", "analytics", "html", r"googletagmanager\.com"),
    ("Hotjar", "analytics", "html", r"static\.hotjar\.com"),
    ("jQuery", "library", "html", r"jquery(?:-|\.)[0-9]|jquery\.min\.js"),
    ("Bootstrap", "library", "html", r"bootstrap(?:\.min)?\.css"),
    ("Tailwind CSS", "library", "html", r"tailwindcss|--tw-"),
    ("Varnish", "cdn", "header:via", r"varnish"),
    ("Vercel", "hosting", "header:server", r"Vercel"),
    ("Netlify", "hosting", "header:server", r"Netlify"),
]

_SERVER_VERSION = re.compile(r"([A-Za-z-]+)[/ ]([0-9][0-9A-Za-z.\-_]+)")


class TechDetectModule(BaseModule):
    name = "tech"
    description = "Detect CMS, frameworks, CDN, analytics and server software from the response."
    rate_limit = 0.5
    supported_types = (TargetType.DOMAIN,)
    category = "technology"

    async def run(self, target: str) -> ModuleResult:
        url = f"https://{target}"
        async with make_client(timeout=15.0) as client:
            try:
                await self._rate_limited()
                resp = await client.get(url)
            except Exception as exc:
                return self.failed(target, f"Request failed: {exc}")

        html = resp.text[:400_000]
        headers = {k.lower(): v for k, v in resp.headers.items()}
        cookies = "; ".join(resp.headers.get_list("set-cookie")) if hasattr(resp.headers, "get_list") else ""

        detected: dict[str, set[str]] = {}
        for name, category, kind, pattern in FINGERPRINTS:
            haystack = ""
            if kind == "html":
                haystack = html
            elif kind == "cookie":
                haystack = cookies
            elif kind.startswith("header:"):
                haystack = headers.get(kind.split(":", 1)[1], "")
            if haystack and re.search(pattern, haystack, re.IGNORECASE):
                detected.setdefault(category, set()).add(name)

        # Version extraction from server / x-powered-by.
        versions = {}
        for hname in ("server", "x-powered-by"):
            if hname in headers:
                for m in _SERVER_VERSION.finditer(headers[hname]):
                    versions[m.group(1)] = m.group(2)

        # Generator meta tag.
        gen = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', html, re.I)
        if gen:
            detected.setdefault("generator", set()).add(gen.group(1))

        result = {k: sorted(v) for k, v in detected.items()}
        flat = sorted({t for s in detected.values() for t in s})
        data = {
            "technologies": result,
            "all": flat,
            "versions": versions,
            "server": headers.get("server"),
            "powered_by": headers.get("x-powered-by"),
            "count": len(flat),
        }
        if not flat and not versions:
            return self.ok(target, data, confidence=0.4, tags=["technology"])
        return self.ok(target, data, tags=["technology"])
