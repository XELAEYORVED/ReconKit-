"""HTTP security headers audit.

Performs a single GET to the target's HTTPS endpoint and scores the presence
and quality of security headers (HSTS, CSP, X-Frame-Options, etc.) plus
cookie flags. Passive: one ordinary web request, no probing.
"""

from __future__ import annotations

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client

# header -> (points if missing, human label)
SECURITY_HEADERS = {
    "strict-transport-security": (20, "HSTS"),
    "content-security-policy": (20, "Content-Security-Policy"),
    "x-frame-options": (10, "X-Frame-Options"),
    "x-content-type-options": (10, "X-Content-Type-Options"),
    "referrer-policy": (10, "Referrer-Policy"),
    "permissions-policy": (10, "Permissions-Policy"),
    "cross-origin-opener-policy": (5, "COOP"),
    "cross-origin-resource-policy": (5, "CORP"),
}


class HeadersAuditModule(BaseModule):
    name = "headers"
    description = "Audit HTTP security headers (HSTS, CSP, X-Frame, CORS, cookies) and grade."
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

        headers = {k.lower(): v for k, v in resp.headers.items()}
        present = {}
        missing = []
        penalty = 0
        for h, (pts, label) in SECURITY_HEADERS.items():
            if h in headers:
                present[label] = headers[h]
            else:
                missing.append(label)
                penalty += pts

        # Cookie flag analysis.
        set_cookies = resp.headers.get_list("set-cookie") if hasattr(resp.headers, "get_list") else []
        cookie_issues = []
        for c in set_cookies:
            low = c.lower()
            cname = c.split("=", 1)[0]
            flags = []
            if "secure" not in low:
                flags.append("missing Secure")
            if "httponly" not in low:
                flags.append("missing HttpOnly")
            if "samesite" not in low:
                flags.append("missing SameSite")
            if flags:
                cookie_issues.append({"cookie": cname, "issues": flags})

        cors = headers.get("access-control-allow-origin")
        cors_wildcard = cors == "*"
        if cors_wildcard:
            penalty += 5

        score = max(0, 100 - penalty - (5 if cookie_issues else 0))
        grade = (
            "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60
            else "D" if score >= 40 else "F"
        )

        data = {
            "final_url": str(resp.url),
            "status_code": resp.status_code,
            "server": headers.get("server"),
            "present": present,
            "missing": missing,
            "cookie_issues": cookie_issues,
            "cors_allow_origin": cors,
            "cors_wildcard": cors_wildcard,
            "score": score,
            "grade": grade,
        }
        return self.ok(target, data, tags=["headers", "technology", "security"])
