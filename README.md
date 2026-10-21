# ReconKit — Passive OSINT Reconnaissance Toolkit

> **ReconKit — Passive OSINT Only. Usage responsable et légal uniquement / Responsible and lawful use only.**

ReconKit combines a powerful **Python CLI** with a modern **React dashboard** for
**100% passive** reconnaissance. It only queries public DNS, public HTTP
endpoints, and public OSINT APIs — **no active scanning, intrusion, fuzzing, or
direct interaction** with target systems.

## Features

- **18 passive modules**: WHOIS/RDAP, DNS, subdomains (crt.sh/HackerTarget/RapidDNS),
  certificate transparency, tech detection, security-headers audit, Wayback,
  email harvesting, social-profile discovery, metadata extraction, Google dorking,
  IP geolocation/ASN, reputation (AbuseIPDB/VirusTotal/OTX), breach check (HIBP),
  Shodan (keyless InternetDB fallback), GitHub recon, pastebin monitor, BGP network map.
- **Async engine** with per-source rate limiting + exponential backoff, result caching,
  cross-module enrichment, a relation graph, and a 0–100 **Threat Score**.
- **Works with zero API keys** (reduced capability); keys unlock advanced modules.
- **Realtime web dashboard**: live scan progress over WebSocket, interactive relation
  graph, geo map, network map, timeline, scan comparison/diff, history, export panel.
- **Reports**: JSON, HTML, Markdown, PDF. **Threat-intel export**: CSV, STIX 2.1, MISP.
- **FastAPI** backend with optional JWT multi-user auth and encrypted API-key storage.

## Quick start (Docker)

```bash
cp .env.example .env     # optional: add API keys
docker compose up --build
# UI + API: http://localhost:8000   (standalone frontend also on :3000)
```

## Local development

**Backend**
```bash
python -m venv .venv && . .venv/Scripts/activate   # or source .venv/bin/activate
pip install -e ".[dev]"
reconkit serve --reload                            # http://localhost:8000
```

**Frontend**
```bash
cd web
npm install
npm run dev                                        # http://localhost:3000 (proxies API)
# or: npm run build   -> served by the backend at :8000
```

## CLI

```bash
reconkit scan example.com                          # full auto scan
reconkit scan example.com -m whois,dns,subdomains  # specific modules
reconkit scan user@example.com                     # email (modules auto-adapted)
reconkit scan --type username johndoe              # username → social profiles
reconkit scan 8.8.8.8                              # IP
reconkit compare scan-001 scan-002                 # diff two scans
reconkit export scan-001 -f pdf                    # report
reconkit export scan-001 -f stix                   # threat-intel
reconkit list                                      # saved scans
reconkit modules                                   # list all modules
reconkit serve --port 8000                         # web server
```

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/scans` | Launch a scan (progress streams over WS) |
| GET | `/api/scans` · `/api/scans/{id}` | List / detail |
| GET | `/api/scans/{id}/results` · `/graph` | Results / relation graph |
| DELETE | `/api/scans/{id}` | Delete |
| GET | `/api/compare/{id1}/{id2}` | Diff two scans |
| GET | `/api/reports/{id}?format=…` | json/html/md/pdf/csv/stix/misp |
| WS | `/ws/scan/{id}` | Realtime scan events |

## Configuration

All settings come from environment variables (prefix `RECONKIT_`) and/or `.env`;
API keys use bare names (`SHODAN_API_KEY`, `VIRUSTOTAL_API_KEY`, `HIBP_API_KEY`,
`HUNTER_API_KEY`, `ABUSEIPDB_API_KEY`, `OTX_API_KEY`, `GITHUB_TOKEN`,
`GOOGLE_CSE_API_KEY`/`GOOGLE_CSE_ID`, `IPINFO_TOKEN`). Keys can also be managed
(encrypted) from the Settings page. Set `RECONKIT_REQUIRE_AUTH=true` to enable JWT auth.

## Tests

```bash
pytest           # hermetic: mocked HTTP + offline fake module
```

## Legal & ethics

ReconKit is for authorized security assessments, research, and education. You are
responsible for ensuring you have permission to gather information about any target.
Passive-only by design.

## License

MIT
