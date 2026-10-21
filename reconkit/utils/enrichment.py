"""Cross-module enrichment and threat scoring.

After all modules run, this correlates their results (linking subdomains to
IPs to ASNs to services), builds the relation graph consumed by the frontend,
and computes an overall Threat Score (0-100).
"""

from __future__ import annotations

from typing import Any

from ..modules.base import ModuleResult


def _by_name(results: list[ModuleResult]) -> dict[str, ModuleResult]:
    return {r.module_name: r for r in results if r.status == "ok"}


def compute_threat_score(results: list[ModuleResult]) -> tuple[int, list[dict[str, Any]]]:
    """Return (score 0-100, list of contributing factors)."""
    score = 0
    factors: list[dict[str, Any]] = []
    by = _by_name(results)

    def add(points: int, reason: str) -> None:
        nonlocal score
        score += points
        factors.append({"points": points, "reason": reason})

    # Missing security headers.
    if "headers" in by:
        hdr = by["headers"].data
        missing = hdr.get("missing", [])
        if missing:
            add(min(20, len(missing) * 3), f"{len(missing)} security headers missing")
        if hdr.get("cors_wildcard"):
            add(5, "CORS allows any origin (*)")
        if hdr.get("cookie_issues"):
            add(5, "Cookies missing security flags")

    # Shodan exposure.
    if "shodan" in by:
        sh = by["shodan"].data
        ports = sh.get("ports", [])
        vulns = sh.get("vulns", [])
        risky = [p for p in ports if p in (21, 23, 3389, 3306, 5432, 6379, 9200, 27017, 11211)]
        if risky:
            add(min(20, len(risky) * 5), f"Sensitive ports exposed: {risky}")
        if vulns:
            add(min(25, len(vulns) * 5), f"{len(vulns)} known CVEs reported by Shodan")

    # Data leaks.
    if "leak_check" in by:
        lk = by["leak_check"].data
        if lk.get("breached"):
            add(min(20, lk.get("breach_count", 0) * 4), f"{lk.get('breach_count')} data breaches")

    # Reputation.
    if "reputation" in by:
        rep = by["reputation"].data
        signals = rep.get("malicious_signals", 0)
        if signals:
            add(min(20, signals * 8), f"{signals} negative reputation signals")

    # Certificate issues.
    if "cert_transparency" in by:
        # crt.sh doesn't give live validity; flag very high SAN sprawl as mild risk.
        san = by["cert_transparency"].data.get("san_count", 0)
        if san > 200:
            add(5, f"Large certificate SAN sprawl ({san} hostnames)")

    # GitHub secrets.
    if "github" in by:
        gh = by["github"].data
        hits = gh.get("secret_hit_count", 0)
        if hits:
            add(min(20, hits * 5), f"{hits} potential secret leaks on GitHub")

    # Obsolete tech (very rough heuristic on versions).
    if "tech" in by:
        versions = by["tech"].data.get("versions", {})
        for name, ver in versions.items():
            if name.lower() in ("php", "openssl", "apache", "nginx") and ver.startswith(("1.", "2.", "5.")):
                add(3, f"Potentially outdated {name} {ver}")

    # Dork / pastebin exposure.
    if by.get("google_dork") and by["google_dork"].data.get("finding_count", 0):
        add(min(15, by["google_dork"].data["finding_count"]), "Sensitive pages exposed via dorks")
    if by.get("pastebin") and by["pastebin"].data.get("hit_count", 0):
        add(min(15, by["pastebin"].data["hit_count"] * 3), "Mentions found in public pastes")

    return min(100, score), factors


def build_relation_graph(target: str, results: list[ModuleResult]) -> dict[str, Any]:
    """Build a node/edge graph linking the discovered entities.

    Node categories map to UI colours; severity hints come from the threat
    factors. Shape: {"nodes": [...], "edges": [...]}.
    """
    by = _by_name(results)
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def node(nid: str, label: str, ntype: str, severity: str = "safe", **extra):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": label, "type": ntype,
                          "severity": severity, **extra}
        return nid

    def edge(src: str, dst: str, label: str = ""):
        edges.append({"source": src, "target": dst, "label": label})

    root = node(f"target:{target}", target, "target", "safe")

    # DNS: A records -> IP nodes.
    if "dns" in by:
        dns = by["dns"].data
        for ip in dns.get("ipv4", []):
            ipn = node(f"ip:{ip}", ip, "ip")
            edge(root, ipn, "A")
        for mx in dns.get("records", {}).get("MX", []):
            host = mx.split()[-1].rstrip(".")
            if not host:  # skip RFC 7505 "null MX" (0 .)
                continue
            mxn = node(f"mx:{host}", host, "mx", "attention")
            edge(root, mxn, "MX")

    # Subdomains -> IPs.
    if "subdomains" in by:
        for sub, ips in by["subdomains"].data.get("live", {}).items():
            sn = node(f"sub:{sub}", sub, "subdomain")
            edge(root, sn, "subdomain")
            for ip in ips:
                ipn = node(f"ip:{ip}", ip, "ip")
                edge(sn, ipn, "resolves")

    # IP geo / ASN.
    if "ip_geo" in by:
        g = by["ip_geo"].data
        ip = g.get("ip")
        if ip:
            ipn = node(f"ip:{ip}", ip, "ip")
            if g.get("asn"):
                an = node(f"asn:{g['asn']}", f"{g['asn']} {g.get('as_name') or ''}".strip(), "asn")
                edge(ipn, an, "ASN")
            if g.get("city") or g.get("country"):
                loc = f"{g.get('city') or ''}, {g.get('country') or ''}".strip(", ")
                gn = node(f"geo:{loc}", loc, "geo")
                edge(ipn, gn, "geo")

    # Shodan services -> ports.
    if "shodan" in by:
        sh = by["shodan"].data
        ip = sh.get("ip")
        ipn = node(f"ip:{ip}", ip or "?", "ip")
        for port in sh.get("ports", []):
            sev = "critical" if port in (21, 23, 3389, 3306, 6379) else "attention"
            pn = node(f"port:{ip}:{port}", f"Port {port}", "service", sev)
            edge(ipn, pn, "open")
        for v in sh.get("vulns", [])[:15]:
            vn = node(f"cve:{v}", v, "vuln", "critical")
            edge(ipn, vn, "vuln")

    # Emails + leaks.
    if "email" in by:
        for em in by["email"].data.get("emails", [])[:25]:
            en = node(f"email:{em}", em, "email", "attention")
            edge(root, en, "email")
    if "leak_check" in by and by["leak_check"].data.get("breached"):
        ln = node("leak:breaches", f"{by['leak_check'].data.get('breach_count')} breaches",
                  "leak", "critical")
        edge(root, ln, "breach")

    # GitHub.
    if "github" in by and by["github"].data.get("secret_hit_count", 0):
        gn = node("github:secrets", f"{by['github'].data['secret_hit_count']} secret hits",
                  "github", "critical")
        edge(root, gn, "github")

    return {"nodes": list(nodes.values()), "edges": edges}


def build_summary(target: str, results: list[ModuleResult], score: int,
                  factors: list[dict]) -> dict[str, Any]:
    by = _by_name(results)
    ok = [r.module_name for r in results if r.status == "ok"]
    errors = [{"module": r.module_name, "error": r.error}
              for r in results if r.status == "error"]
    skipped = [{"module": r.module_name, "reason": r.error}
               for r in results if r.status == "skipped"]
    highlights = {
        "subdomain_count": by.get("subdomains").data.get("count") if "subdomains" in by else 0,
        "open_ports": by.get("shodan").data.get("ports") if "shodan" in by else [],
        "emails": by.get("email").data.get("email_count") if "email" in by else 0,
        "breaches": by.get("leak_check").data.get("breach_count") if "leak_check" in by else 0,
        "technologies": by.get("tech").data.get("all") if "tech" in by else [],
        "header_grade": by.get("headers").data.get("grade") if "headers" in by else None,
    }
    return {
        "target": target,
        "threat_score": score,
        "threat_factors": factors,
        "risk_level": risk_level(score),
        "modules_ok": ok,
        "modules_error": errors,
        "modules_skipped": skipped,
        "highlights": highlights,
    }


def risk_level(score: int) -> str:
    if score >= 70:
        return "critical"
    if score >= 40:
        return "high"
    if score >= 20:
        return "medium"
    return "low"
