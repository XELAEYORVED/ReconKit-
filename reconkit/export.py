"""Export formats: CSV, STIX 2.1, MISP event.

Converts a scan result dict into interchange formats for threat-intelligence
platforms. STIX/MISP map discovered indicators (domains, IPs, emails, URLs) to
standard objects.
"""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _indicators(scan: dict[str, Any]) -> dict[str, set[str]]:
    """Collect indicators of interest from module results."""
    ind: dict[str, set[str]] = {"domain": set(), "ipv4": set(), "email": set(), "url": set()}
    ind["domain"].add(scan["target"]) if scan.get("target_type") == "domain" else None
    for r in scan.get("results", []):
        if r["status"] != "ok":
            continue
        d = r["data"]
        name = r["module_name"]
        if name == "dns":
            ind["ipv4"].update(d.get("ipv4", []))
        if name == "subdomains":
            ind["domain"].update(d.get("subdomains", []))
            for ips in d.get("live", {}).values():
                ind["ipv4"].update(ips)
        if name == "ip_geo" and d.get("ip"):
            ind["ipv4"].add(d["ip"])
        if name == "email":
            ind["email"].update(d.get("emails", []))
        if name in ("google_dork", "pastebin"):
            for h in d.get("findings", d.get("hits", [])):
                if h.get("url"):
                    ind["url"].add(h["url"])
    return {k: v for k, v in ind.items() if v}


def to_csv(scan: dict[str, Any]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["module", "status", "confidence", "tags", "key", "value"])
    for r in scan.get("results", []):
        tags = "|".join(r.get("tags", []))
        if r["status"] != "ok":
            writer.writerow([r["module_name"], r["status"], r.get("confidence", 0),
                             tags, "error", r.get("error", "")])
            continue
        for k, v in r["data"].items():
            val = json.dumps(v, default=str) if isinstance(v, (dict, list)) else v
            writer.writerow([r["module_name"], r["status"], r.get("confidence", 1.0),
                             tags, k, str(val)[:2000]])
    return buf.getvalue()


def to_stix(scan: dict[str, Any]) -> str:
    """Produce a STIX 2.1 bundle of indicators."""
    objects: list[dict[str, Any]] = []
    now = _now()
    identity_id = f"identity--{uuid.uuid4()}"
    objects.append({
        "type": "identity", "spec_version": "2.1", "id": identity_id,
        "created": now, "modified": now, "name": "ReconKit",
        "identity_class": "system",
    })

    pattern_for = {
        "domain": lambda v: f"[domain-name:value = '{v}']",
        "ipv4": lambda v: f"[ipv4-addr:value = '{v}']",
        "email": lambda v: f"[email-addr:value = '{v}']",
        "url": lambda v: f"[url:value = '{v}']",
    }
    for itype, values in _indicators(scan).items():
        for v in sorted(values):
            objects.append({
                "type": "indicator", "spec_version": "2.1",
                "id": f"indicator--{uuid.uuid4()}",
                "created": now, "modified": now,
                "created_by_ref": identity_id,
                "name": f"{itype}: {v}",
                "pattern": pattern_for[itype](v),
                "pattern_type": "stix",
                "valid_from": now,
                "labels": ["osint", f"reconkit-{scan.get('target_type')}"],
                "confidence": int(scan.get("threat_score", 0)),
            })

    bundle = {"type": "bundle", "id": f"bundle--{uuid.uuid4()}", "objects": objects}
    return json.dumps(bundle, indent=2)


def to_misp(scan: dict[str, Any]) -> str:
    """Produce a MISP event JSON."""
    now = datetime.now(timezone.utc)
    type_map = {"domain": "domain", "ipv4": "ip-dst", "email": "email-src", "url": "url"}
    attributes = []
    for itype, values in _indicators(scan).items():
        for v in sorted(values):
            attributes.append({
                "type": type_map[itype],
                "category": "Network activity" if itype in ("domain", "ipv4", "url")
                else "Payload delivery",
                "value": v,
                "to_ids": itype in ("ipv4", "url"),
                "comment": f"ReconKit passive OSINT ({scan.get('id')})",
            })
    event = {
        "Event": {
            "info": f"ReconKit passive recon — {scan['target']}",
            "date": now.strftime("%Y-%m-%d"),
            "threat_level_id": "3",
            "analysis": "2",
            "distribution": "0",
            "Tag": [{"name": "osint"}, {"name": "reconkit"},
                    {"name": f"risk:{scan.get('summary', {}).get('risk_level', 'low')}"}],
            "Attribute": attributes,
        }
    }
    return json.dumps(event, indent=2)


def export(scan: dict[str, Any], fmt: str) -> tuple[bytes, str]:
    fmt = fmt.lower()
    if fmt == "csv":
        return to_csv(scan).encode(), "text/csv"
    if fmt == "stix":
        return to_stix(scan).encode(), "application/json"
    if fmt == "misp":
        return to_misp(scan).encode(), "application/json"
    raise ValueError(f"Unsupported export format: {fmt}")
