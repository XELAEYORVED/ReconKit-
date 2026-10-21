"""Report generation: JSON, Markdown, HTML, PDF.

Takes a persisted scan (dict form) and renders a human-readable report in the
requested format. PDF uses WeasyPrint if installed, otherwise falls back to
HTML with a clear notice.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from jinja2 import Environment

from . import ETHICAL_BANNER, __version__

_HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>ReconKit Report — {{ scan.target }}</title>
<style>
 body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0a0a0f;color:#d6f5e3;margin:0;padding:2rem;}
 h1,h2,h3{color:#39ff14;} a{color:#22d3ee;}
 .banner{background:#111827;border:1px solid #39ff14;padding:.6rem 1rem;border-radius:8px;margin-bottom:1.5rem;font-size:.85rem;color:#9ca3af;}
 .score{font-size:3rem;font-weight:700;}
 .risk-critical{color:#ef4444;} .risk-high{color:#f97316;} .risk-medium{color:#eab308;} .risk-low{color:#22c55e;}
 table{border-collapse:collapse;width:100%;margin:.5rem 0 1.5rem;}
 th,td{border:1px solid #1f2937;padding:.4rem .6rem;text-align:left;font-size:.85rem;vertical-align:top;}
 th{background:#111827;color:#39ff14;}
 .card{background:#0f1117;border:1px solid #1f2937;border-radius:10px;padding:1rem 1.25rem;margin-bottom:1rem;}
 code{background:#111827;padding:.1rem .3rem;border-radius:4px;}
 pre{background:#0d1117;padding:1rem;border-radius:8px;overflow:auto;font-size:.75rem;}
 .tag{display:inline-block;background:#1f2937;color:#22d3ee;border-radius:12px;padding:.1rem .6rem;margin:.1rem;font-size:.7rem;}
</style></head><body>
<div class="banner">{{ banner }}</div>
<h1>ReconKit Report</h1>
<div class="card">
  <p><strong>Target:</strong> <code>{{ scan.target }}</code> ({{ scan.target_type }})</p>
  <p><strong>Scan ID:</strong> {{ scan.id }}</p>
  <p><strong>Generated:</strong> {{ generated }} · ReconKit v{{ version }}</p>
  <p class="score risk-{{ summary.risk_level }}">{{ scan.threat_score }}/100
     <span style="font-size:1rem">({{ summary.risk_level | upper }})</span></p>
</div>

<h2>Threat Factors</h2>
<table><tr><th>Points</th><th>Reason</th></tr>
{% for f in summary.threat_factors %}<tr><td>+{{ f.points }}</td><td>{{ f.reason }}</td></tr>{% endfor %}
{% if not summary.threat_factors %}<tr><td colspan=2>No risk factors detected.</td></tr>{% endif %}
</table>

<h2>Module Results</h2>
{% for r in results %}
<div class="card">
  <h3>{{ r.module_name }} <span style="font-size:.7rem;color:#6b7280">[{{ r.status }}]</span></h3>
  {% for t in r.tags %}<span class="tag">{{ t }}</span>{% endfor %}
  {% if r.status == 'ok' %}<pre>{{ r.data | tojson(indent=2) }}</pre>
  {% else %}<p style="color:#f97316">{{ r.error }}</p>{% endif %}
</div>
{% endfor %}
</body></html>"""


def _env() -> Environment:
    env = Environment(autoescape=True)
    env.filters["tojson"] = lambda v, indent=None: json.dumps(v, indent=indent, default=str)
    return env


def render_json(scan: dict[str, Any]) -> str:
    return json.dumps(scan, indent=2, default=str)


def render_markdown(scan: dict[str, Any]) -> str:
    s = scan.get("summary", {})
    lines = [
        f"# ReconKit Report — {scan['target']}",
        "",
        f"> {ETHICAL_BANNER}",
        "",
        f"- **Target:** `{scan['target']}` ({scan.get('target_type')})",
        f"- **Scan ID:** {scan.get('id')}",
        f"- **Threat Score:** **{scan.get('threat_score')}/100** "
        f"({s.get('risk_level', 'n/a').upper()})",
        f"- **Generated:** {datetime.now(timezone.utc).isoformat()} · ReconKit v{__version__}",
        "",
        "## Threat Factors",
        "",
    ]
    factors = s.get("threat_factors", [])
    if factors:
        lines += [f"- **+{f['points']}** — {f['reason']}" for f in factors]
    else:
        lines.append("- No risk factors detected.")
    lines += ["", "## Module Results", ""]
    for r in scan.get("results", []):
        lines.append(f"### {r['module_name']} _[{r['status']}]_")
        if r["status"] == "ok":
            lines += ["", "```json", json.dumps(r["data"], indent=2, default=str)[:4000], "```", ""]
        else:
            lines += ["", f"_Error: {r.get('error')}_", ""]
    return "\n".join(lines)


def render_html(scan: dict[str, Any]) -> str:
    tmpl = _env().from_string(_HTML_TEMPLATE)
    return tmpl.render(
        scan=scan,
        summary=scan.get("summary", {}),
        results=scan.get("results", []),
        banner=ETHICAL_BANNER,
        version=__version__,
        generated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


def render_pdf(scan: dict[str, Any]) -> bytes:
    html = render_html(scan)
    try:
        from weasyprint import HTML  # optional dependency

        return HTML(string=html).write_pdf()
    except Exception as exc:
        notice = (
            f"<!-- PDF engine unavailable ({exc}); returning HTML. "
            "Install the 'pdf' extra: pip install reconkit[pdf] -->\n"
        )
        return (notice + html).encode("utf-8")


def render(scan: dict[str, Any], fmt: str) -> tuple[bytes, str]:
    """Return (content_bytes, media_type) for the requested format."""
    fmt = fmt.lower()
    if fmt == "json":
        return render_json(scan).encode(), "application/json"
    if fmt in ("md", "markdown"):
        return render_markdown(scan).encode(), "text/markdown"
    if fmt == "html":
        return render_html(scan).encode(), "text/html"
    if fmt == "pdf":
        return render_pdf(scan), "application/pdf"
    raise ValueError(f"Unsupported report format: {fmt}")
