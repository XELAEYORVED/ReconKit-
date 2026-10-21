# Prompt — ReconKit : Outil OSINT de Reconnaissance Passive

Tu es un développeur senior fullstack Python + React. Tu vas construire **ReconKit**, un outil OSINT (Open Source Intelligence) de reconnaissance passive. L'outil combine une **CLI Python** puissante et une **interface web moderne** avec tableau de bord temps réel.

> **Règle absolue** : ReconKit ne fait que de la reconnaissance **passive**. Aucun scan actif, aucune intrusion, aucun fuzzing, aucune interaction directe avec les systèmes cibles au-delà de requêtes DNS/HTTP publiques. Affiche un bandeau éthique au lancement.

---

## 1. Architecture technique

```
reconkit/
├── reconkit/
│   ├── __init__.py
│   ├── cli.py                 # CLI click
│   ├── engine.py              # Moteur asyncio d'orchestration
│   ├── config.py              # Configuration YAML + .env
│   ├── models.py              # SQLAlchemy models
│   ├── database.py            # Session SQLite/PostgreSQL
│   ├── report.py              # Génération de rapports (JSON, HTML, PDF, Markdown)
│   ├── export.py              # Export CSV, STIX, MISP
│   ├── utils/
│   │   ├── rate_limiter.py    # Rate limiting par source
│   │   ├── cache.py           # Cache Redis/disque des résultats
│   │   ├── validators.py      # Validation d'entrées (domaine, IP, email)
│   │   └── enrichment.py      # Corrélation et enrichissement croisé
│   └── modules/
│       ├── __init__.py
│       ├── base.py            # Classe abstraite BaseModule
│       ├── whois_lookup.py
│       ├── dns_enum.py
│       ├── subdomain_enum.py
│       ├── cert_transparency.py
│       ├── wayback_machine.py
│       ├── tech_detect.py
│       ├── headers_audit.py
│       ├── email_harvest.py
│       ├── social_media.py     # Recherche de profils sociaux (username OSINT)
│       ├── metadata_extract.py # Extraction de métadonnées (images, PDF, documents)
│       ├── google_dorking.py   # Google Dorks automatisés (CSE API)
│       ├── ip_geolocation.py   # Géolocalisation IP + ASN + range
│       ├── reputation.py       # Réputation IP/domaine (AbuseIPDB, VirusTotal)
│       ├── leak_check.py       # Vérification de fuites de données (Have I Been Pwned API)
│       ├── shodan_recon.py     # Intégration Shodan (ports, services, bannières)
│       ├── github_recon.py     # Recherche de secrets dans les repos publics (dorks GitHub)
│       ├── pastebin_monitor.py # Recherche dans les pastebins publics
│       └── network_map.py      # Cartographie réseau (AS, BGP, voisinage)
├── server/
│   ├── __init__.py
│   ├── main.py                # FastAPI app
│   ├── routes/
│   │   ├── scans.py           # CRUD scans
│   │   ├── results.py         # Résultats + filtres
│   │   ├── reports.py         # Téléchargement rapports
│   │   ├── compare.py         # Comparaison entre scans (diff)
│   │   └── ws.py              # WebSocket temps réel
│   └── middleware/
│       ├── auth.py            # Auth JWT (multi-utilisateurs)
│       └── cors.py
├── web/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── stores/            # Zustand pour state management
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Dashboard.tsx          # Vue d'ensemble
│   │   │   ├── ScanForm.tsx           # Formulaire de lancement
│   │   │   ├── ScanProgress.tsx       # Barre de progression temps réel
│   │   │   ├── ResultsTable.tsx       # Tableau filtrable/triable
│   │   │   ├── RelationGraph.tsx      # Graphe de relations (D3.js / vis.js)
│   │   │   ├── DomainTimeline.tsx     # Timeline historique du domaine
│   │   │   ├── ThreatScore.tsx        # Score de risque visuel
│   │   │   ├── NetworkMap.tsx         # Carte réseau interactive
│   │   │   ├── GeoMap.tsx             # Carte géographique (Leaflet)
│   │   │   ├── ExportPanel.tsx        # Panel d'export multi-format
│   │   │   ├── CompareView.tsx        # Comparaison de deux scans
│   │   │   └── ScanHistory.tsx        # Historique des scans
│   │   └── pages/
│   │       ├── Home.tsx
│   │       ├── Scan.tsx
│   │       ├── Results.tsx
│   │       ├── History.tsx
│   │       └── Settings.tsx
│   └── public/
├── tests/
│   ├── test_modules/
│   ├── test_engine.py
│   └── test_api.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
└── .env.example
```

---

## 2. Backend Python — Détails

### 2.1 Classe abstraite `BaseModule`
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
import asyncio

@dataclass
class ModuleResult:
    module_name: str
    target: str
    data: dict[str, Any]
    raw: Any = None
    confidence: float = 1.0  # 0-1, fiabilité du résultat
    tags: list[str] = None   # ex: ["dns", "infrastructure"]

class BaseModule(ABC):
    name: str
    description: str
    passive_only: bool = True  # DOIT rester True
    rate_limit: float = 1.0    # secondes entre requêtes
    requires_api_key: bool = False

    @abstractmethod
    async def run(self, target: str) -> ModuleResult:
        ...

    @abstractmethod
    def validate_target(self, target: str) -> bool:
        ...
```

### 2.2 Les 18 modules

| # | Module | Source/API | Données récoltées |
|---|--------|-----------|-------------------|
| 1 | **WHOIS Lookup** | python-whois + RDAP | Registrar, dates, contacts, name servers |
| 2 | **DNS Enumeration** | dnspython | A, AAAA, MX, NS, TXT, SOA, CNAME, SRV, DMARC, SPF |
| 3 | **Subdomain Enumeration** | crt.sh, DNSDumpster, Sublist3r passif, RapidDNS | Liste de sous-domaines découverts |
| 4 | **Certificate Transparency** | crt.sh API | Tous les certificats émis, SAN, émetteur, dates |
| 5 | **Wayback Machine** | Wayback CDX API | Snapshots historiques, URLs archivées, changements |
| 6 | **Tech Detection** | Wappalyzer (rules), headers, HTML patterns | CMS, frameworks, CDN, analytics, serveur |
| 7 | **Headers Security Audit** | Requête HEAD/GET | HSTS, CSP, X-Frame, CORS, cookies flags, score |
| 8 | **Email Harvesting** | Hunter.io, pattern guessing, crt.sh | Adresses email, pattern format, confiance |
| 9 | **Social Media Profiling** | Namechk-style checks, API publiques | Présence sur réseaux sociaux par username |
| 10 | **Metadata Extraction** | ExifTool, python-docx, PyPDF2 | Métadonnées images/docs (GPS, auteur, logiciel) |
| 11 | **Google Dorking** | Google CSE API | Pages sensibles, fichiers exposés, répertoires |
| 12 | **IP Geolocation & ASN** | ip-api, ipinfo.io, BGPView | Localisation, ASN, range, organisation |
| 13 | **Reputation Check** | AbuseIPDB, VirusTotal, AlienVault OTX | Score de réputation, signalements, malware |
| 14 | **Leak Check** | Have I Been Pwned API (k-anonymity) | Fuites de données associées aux emails |
| 15 | **Shodan Recon** | Shodan API | Ports ouverts, services, bannières, vulns connues |
| 16 | **GitHub Recon** | GitHub Search API | Secrets exposés, mentions du domaine, dorks |
| 17 | **Pastebin Monitor** | Google CSE + Paste sites | Mentions dans pastebins publics |
| 18 | **Network Mapping** | BGPView, RIPE, HE.net | Voisinage réseau, peers BGP, préfixes |

### 2.3 Moteur d'orchestration (`engine.py`)
```python
class ReconEngine:
    """Orchestre les modules en parallèle avec gestion de priorités."""

    async def run_scan(self, target: str, modules: list[str] | None = None,
                       max_concurrency: int = 5, timeout: int = 120):
        # 1. Valider la cible (domaine, IP, email, username)
        # 2. Détecter automatiquement le type de cible
        # 3. Sélectionner les modules pertinents si non spécifiés
        # 4. Lancer en parallèle avec semaphore asyncio
        # 5. Streamer les résultats via WebSocket au fur et à mesure
        # 6. Enrichir : croiser les résultats entre modules
        # 7. Calculer le score de menace global
        # 8. Sauvegarder en DB + générer le rapport
```

### 2.4 Score de menace
Calculer un **Threat Score** (0-100) basé sur :
- Headers de sécurité manquants (+points)
- Ports/services exposés via Shodan (+points)
- Fuites de données trouvées (+points)
- Réputation négative (+points)
- Certificats expirés ou invalides (+points)
- Secrets trouvés sur GitHub (+points)
- Technologies obsolètes détectées (+points)

### 2.5 CLI (`cli.py`)
```bash
# Scan complet d'un domaine
reconkit scan example.com

# Scan avec modules spécifiques
reconkit scan example.com --modules whois,dns,subdomains,shodan

# Scan d'un email (modules adaptés automatiquement)
reconkit scan user@example.com

# Scan d'un username (réseaux sociaux)
reconkit scan --type username johndoe

# Scan d'une IP
reconkit scan 8.8.8.8

# Comparer deux scans
reconkit compare scan-001 scan-002

# Export
reconkit export scan-001 --format pdf
reconkit export scan-001 --format stix  # Format threat intel

# Lancer le serveur web
reconkit serve --port 8000
```

---

## 3. Frontend React — Détails

### 3.1 Stack
- **React 18** + TypeScript
- **Vite** pour le build
- **Tailwind CSS** — thème cyber dark (fond #0a0a0f, accents verts/cyan)
- **Zustand** pour le state management
- **React Query** pour le cache API
- **D3.js** ou **vis.js** pour le graphe de relations
- **Leaflet** pour la carte géographique
- **Recharts** pour les graphiques de stats

### 3.2 Pages et composants clés

**Dashboard (page d'accueil)**
- Statistiques globales (scans lancés, domaines analysés, menaces détectées)
- Derniers scans avec statut et score
- Graphique d'activité (scans/jour)

**Page Scan**
- Champ de saisie intelligent (auto-détecte domaine/IP/email/username)
- Sélection des modules (toggles avec descriptions)
- Progression en temps réel via WebSocket :
  - Barre de progression globale
  - Statut de chaque module (⏳ en cours, ✅ terminé, ❌ erreur)
  - Résultats qui apparaissent au fur et à mesure

**Page Résultats**
- **Onglet Synthèse** : Threat Score (jauge circulaire), résumé exécutif
- **Onglet Infrastructure** : DNS, sous-domaines, IPs, carte réseau
- **Onglet Technologies** : Stack détectée, versions, vulnérabilités connues
- **Onglet Identité** : Emails, profils sociaux, fuites de données
- **Onglet Historique** : Timeline Wayback, changements DNS historiques
- **Onglet Carte** : Géolocalisation des serveurs sur carte interactive
- **Onglet Graphe** : Graphe de relations interactif (domaine → sous-domaines → IPs → ASN → services)
- **Onglet Brut** : Toutes les données JSON, filtrable

**Page Comparaison**
- Diff visuel entre deux scans du même domaine
- Nouveaux sous-domaines, services apparus/disparus, changements de score

**Page Historique**
- Tableau de tous les scans avec recherche/filtres
- Tags, notes, favoris

**Page Settings**
- Gestion des clés API (Shodan, VirusTotal, Hunter.io, etc.)
- Configuration des rate limits
- Préférences d'export
- Thème clair/sombre

### 3.3 Graphe de relations
Le composant `RelationGraph.tsx` est le cœur visuel de ReconKit :
```
[Domaine cible]
  ├── [Sous-domaine 1] → [IP 1] → [ASN] → [Geo: Paris]
  │                         └── [Port 443: nginx 1.18]
  │                         └── [Port 22: OpenSSH 8.9]
  ├── [Sous-domaine 2] → [IP 2] → [CDN: Cloudflare]
  ├── [MX: mail.example.com] → [IP 3]
  ├── [Email: admin@example.com] → [Leak: 2 breaches]
  └── [GitHub: 3 mentions] → [Secret trouvé: API key]
```
Noeuds cliquables, zoom, drag, filtres par type. Couleurs par catégorie : vert=safe, orange=attention, rouge=critique.

---

## 4. API FastAPI

```python
# Endpoints principaux
POST   /api/scans              # Lancer un scan
GET    /api/scans              # Lister les scans
GET    /api/scans/{id}         # Détail d'un scan
GET    /api/scans/{id}/results # Résultats d'un scan
DELETE /api/scans/{id}         # Supprimer un scan
GET    /api/compare/{id1}/{id2}# Comparer deux scans
GET    /api/reports/{id}       # Télécharger le rapport
WS     /ws/scan/{id}           # WebSocket temps réel

# WebSocket events
{
  "event": "module_start" | "module_progress" | "module_complete" | "module_error" | "scan_complete",
  "module": "whois",
  "data": { ... },
  "progress": 0.65
}
```

---

## 5. Base de données

SQLite par défaut, PostgreSQL en option. Tables :
- `scans` (id, target, target_type, status, threat_score, started_at, completed_at, config)
- `results` (id, scan_id, module_name, data JSON, confidence, tags, created_at)
- `api_keys` (id, service, key_encrypted, created_at)
- `scan_tags` (scan_id, tag)
- `scan_notes` (id, scan_id, content, created_at)

---

## 6. Docker

```yaml
# docker-compose.yml
version: "3.9"
services:
  backend:
    build: .
    ports: ["8000:8000"]
    volumes: ["./data:/app/data"]
    env_file: .env

  frontend:
    build: ./web
    ports: ["3000:3000"]
    depends_on: [backend]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

Un seul `docker compose up` pour tout lancer.

---

## 7. Contraintes et bonnes pratiques

1. **100% passif** — Aucune requête qui pourrait être considérée comme un scan actif
2. **Rate limiting** — Respecter les limites de chaque API, avec backoff exponentiel
3. **Cache** — Mettre en cache les résultats pour éviter les requêtes inutiles (TTL configurable)
4. **Gestion d'erreurs** — Chaque module doit gérer ses erreurs proprement sans bloquer les autres
5. **Bandeau éthique** au lancement CLI et en header web : "ReconKit — Passive OSINT Only. Usage responsable et légal uniquement."
6. **API keys optionnelles** — L'outil doit fonctionner sans clés API (fonctionnalités réduites), les clés débloquent les modules avancés
7. **Tests** — Pytest avec mocks pour chaque module, tests d'intégration pour l'API
8. **Typage strict** — Mypy, Pydantic pour la validation
9. **Documentation** — Docstrings, README complet, exemples d'utilisation
10. **Export menace** — Support STIX 2.1 pour intégration avec les plateformes de threat intelligence

---

## 8. Étapes de développement (dans cet ordre)

1. Setup projet (pyproject.toml, structure dossiers, Docker base)
2. `BaseModule` + `ReconEngine` + database models
3. Implémenter les 6 modules de base : WHOIS, DNS, Subdomains, Cert Transparency, Tech Detection, Headers
4. CLI avec click
5. FastAPI + WebSocket
6. Frontend React : layout + ScanForm + ScanProgress
7. ResultsTable + onglets de résultats
8. Implémenter les 12 modules avancés : Wayback, Email, Social, Metadata, Google Dorks, IP Geo, Reputation, Leak Check, Shodan, GitHub, Pastebin, Network Map
9. RelationGraph (D3.js) + GeoMap (Leaflet)
10. Système de rapports (JSON, HTML, PDF, Markdown, STIX)
11. Comparaison de scans + historique
12. Threat Score + enrichissement croisé
13. Tests + polish + documentation

Commence par l'étape 1. À chaque étape, montre-moi le code complet et fonctionnel. Pas de placeholder, pas de TODO — du vrai code.
