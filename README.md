# ReconKit — Boîte à outils de reconnaissance OSINT passive

> **ReconKit — OSINT passif uniquement. Usage responsable et légal uniquement.**
>
> **Pas développeur ?** Lis plutôt le **[guide simple (GUIDE.md)](GUIDE.md)** : ce que fait
> ReconKit, comment l'installer et lire les résultats, sans jargon. Ce README-ci est la
> documentation technique.

ReconKit associe une **interface en ligne de commande (CLI) Python** et un **tableau de bord
React** pour faire de la reconnaissance **100 % passive**. Tu lui donnes un domaine, une
adresse IP, un email ou un pseudo : il interroge uniquement le DNS public, des pages web
publiques et des API OSINT publiques. **Aucun scan actif, aucune intrusion, aucun fuzzing,
aucune interaction directe** avec les systèmes de la cible.

## Fonctionnalités

- **19 modules passifs** (voir [Modules](#modules)) : WHOIS/RDAP, DNS, sous-domaines,
  transparence des certificats, détection de technologies, audit des en-têtes de sécurité,
  Wayback Machine, collecte d'emails, profil d'email, réseaux sociaux, métadonnées de
  documents, Google dorking, géolocalisation IP/ASN, réputation, fuites de données, Shodan,
  GitHub, sites de « paste », carte réseau BGP.
- **Détection automatique** du type de cible (domaine / IP / email / pseudo) : seuls les
  modules pertinents sont lancés. Une cible invalide est refusée tout de suite avec un
  message clair.
- **Moteur asynchrone** avec limitation de débit par source et nouvelles tentatives
  progressives (backoff exponentiel), cache des résultats (disque ou Redis), enrichissement
  croisé entre modules, graphe de relations et **score de risque** de 0 à 100 accompagné de
  la liste des facteurs qui l'expliquent.
- **Fonctionne sans aucune clé API** : 15 modules tournent sans clé, dont un profil d'email
  complet. Les clés débloquent le reste et sont **prises en compte immédiatement** (sans
  redémarrage).
- **Tableau de bord web en français** : une fiche lisible par module, progression du scan
  en direct (WebSocket), graphe de relations, carte, carte réseau, chronologie, comparaison
  de scans, historique avec favoris / tags / notes, export. Interface responsive, avec une
  barre d'onglets en bas de l'écran sur mobile.
- **Rapports** : JSON, HTML, Markdown, PDF. **Export threat-intel** : CSV, STIX 2.1, MISP.
- **Backend FastAPI** avec authentification JWT multi-utilisateur optionnelle et stockage
  chiffré des clés API.

## Fonctionnement

```text
cible ──► validation + détection ──► choix des ──► exécution en parallèle (asynchrone,
          (domaine/ip/email/pseudo)   modules       débit limité, mis en cache)
                                                              │
   rapports / exports ◄── base SQLite ◄── enrichissement + score de risque + graphe
                                                              │
                              tableau CLI  ·  tableau de bord web (en direct via WebSocket)
```

| Dossier | Rôle |
| --- | --- |
| `reconkit/` | Cœur : CLI (`cli.py`), moteur, configuration, modèles de base de données, rapports et exports |
| `reconkit/modules/` | Un fichier par module de reconnaissance, tous héritent de `base.py` |
| `reconkit/utils/` | Cache, limiteur de débit, chiffrement, validation, enrichissement / score de risque |
| `server/` | Application FastAPI : routes REST, WebSocket, authentification |
| `web/` | Tableau de bord React 18 + TypeScript + Vite + Tailwind |
| `tests/` | Tests pytest (HTTP simulé, aucun accès réseau nécessaire) |

## Démarrage rapide (Docker)

```bash
cp .env.example .env     # optionnel : ajoute tes clés API
docker compose up --build
# Interface + API : http://localhost:8000   (frontend autonome aussi sur :3000)
```

Docker lance le backend, un cache Redis et le frontend. Les données des scans sont
conservées dans `./data`.

## Développement en local

Il faut **Python 3.11+** et **Node 18+**.

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate                 # Windows  (Linux/macOS : source .venv/bin/activate)
pip install -e ".[dev]"
reconkit serve --reload                # http://localhost:8000  (doc de l'API : /docs)
```

Extras optionnels : `pip install -e ".[metadata]"` (métadonnées PDF/DOCX/images),
`".[pdf]"` (rapports PDF via WeasyPrint), `".[redis]"`, `".[postgres]"`.

### Frontend

```bash
cd web
npm install
npm run dev                            # http://localhost:3000 (redirige vers l'API)
# ou : npm run build   -> servi par le backend sur :8000
```

## Ligne de commande (CLI)

```bash
reconkit scan example.com                          # scan complet automatique
reconkit scan example.com -m whois,dns,subdomains  # seulement certains modules
reconkit scan user@example.com                     # email (email_profile, leak_check, pastebin)
reconkit scan --type username johndoe              # pseudo → réseaux sociaux
reconkit scan 8.8.8.8                              # adresse IP
reconkit scan example.com -o rapport.json --no-save # écrit le JSON sans enregistrer en base
reconkit list                                      # scans enregistrés (avec leurs ID)
reconkit compare scan-<id1> scan-<id2>             # différences entre deux scans
reconkit export scan-<id> -f pdf                   # rapport
reconkit export scan-<id> -f stix -o out.json      # export threat-intel
reconkit modules                                   # liste de tous les modules
reconkit serve --port 8000                         # serveur web
```

Les ID de scan ressemblent à `scan-3f9a1c2b7d4e` (affichés à la fin de chaque scan et par
`reconkit list`).

| Option de `scan` | Rôle |
| --- | --- |
| `-m, --modules` | Noms de modules séparés par des virgules (par défaut : tous ceux qui s'appliquent) |
| `--type` | Force `domain`, `ip`, `email` ou `username` au lieu de la détection automatique |
| `-c, --concurrency` | Nombre maximum de modules lancés en même temps (5 par défaut) |
| `-t, --timeout` | Délai maximum par module, en secondes (120 par défaut) |
| `-o, --output` | Écrit aussi le rapport JSON dans un fichier |
| `--no-save` | N'enregistre pas le scan dans la base de données |

`export -f` accepte `json`, `md`, `html`, `pdf`, `csv`, `stix`, `misp`.

## Modules

| Nom | Cibles | Clé API | Ce qu'il trouve |
| --- | --- | --- | --- |
| `whois` | domaine, ip | — | Registrar, dates, contacts, serveurs DNS (RDAP + WHOIS) |
| `dns` | domaine | — | A/AAAA/MX/NS/TXT/SOA/CNAME/SRV/CAA + SPF et DMARC |
| `subdomains` | domaine | — | Sous-domaines via crt.sh, HackerTarget, RapidDNS |
| `cert_transparency` | domaine | — | Certificats émis, noms couverts (SAN), émetteurs (crt.sh) |
| `tech` | domaine | — | CMS, frameworks, CDN, outils d'analyse, logiciel serveur |
| `headers` | domaine | — | En-têtes de sécurité (HSTS, CSP, CORS, cookies…) + note |
| `wayback` | domaine | — | Captures et URL archivées (index CDX, API de secours si indisponible) |
| `metadata` | domaine | — | Auteur / logiciel / GPS dans les métadonnées de documents publics |
| `email` | domaine | optionnelle (Hunter) | Emails et format d'adresse de l'organisation |
| `github` | domaine | optionnelle (GitHub) | Mentions publiques et fuites de secrets possibles |
| `google_dork` | domaine | **obligatoire** (Google CSE) | Pages sensibles via des recherches Google ciblées |
| `pastebin` | domaine, email | **obligatoire** (Google CSE) | Mentions sur des sites de « paste » publics |
| `ip_geo` | domaine, ip | optionnelle (IPinfo) | Géolocalisation, ASN, hébergeur |
| `network_map` | domaine, ip | — | ASN, plages d'IP annoncées, voisins BGP (RIPEstat) |
| `shodan` | domaine, ip | optionnelle (Shodan) | Ports ouverts, services, CVE (repli gratuit InternetDB sans clé) |
| `reputation` | domaine, ip | optionnelle (AbuseIPDB/VT/OTX) | Signalements d'activité malveillante |
| `email_profile` | email | — | Type de fournisseur (webmail / jetable / domaine propre), MX, SPF, DMARC, profil Gravatar public |
| `leak_check` | email | **obligatoire** (HIBP) | Fuites de données connues |
| `social` | pseudo | — | Profils publics sur les principales plateformes |

Un module dont la clé obligatoire manque apparaît comme `SKIP` (ignoré), pas comme une erreur.
La recherche par nom complet (par exemple « Jean Dupont ») n'est pas prise en charge : une
cible est un seul domaine, une IP, un email ou un pseudo.

## Score de risque

Chaque scan reçoit un score de 0 à 100, calculé en additionnant des facteurs, par exemple :
en-têtes de sécurité manquants, CORS ouvert à tous, ports sensibles exposés (21, 23, 3389,
3306…), CVE connues, fuites de données, mauvaise réputation, secrets trouvés sur GitHub,
logiciels obsolètes, exposition via Google ou des sites de paste, domaine d'email sans
politique DMARC appliquée, fournisseur d'email jetable.

Niveaux : **faible** (< 20), **moyen** (20–39), **élevé** (40–69), **critique** (≥ 70).
Chaque facteur est listé avec ses points : le score est toujours explicable.

## API

Documentation interactive sur `http://localhost:8000/docs`.

| Méthode | Chemin | Rôle |
| --- | --- | --- |
| POST | `/api/scans` | Lance un scan (400 si la cible est invalide ; progression via WS) |
| GET | `/api/scans` · `/api/scans/{id}` | Liste / détail |
| GET | `/api/scans/stats` · `/api/scans/modules` | Statistiques du tableau de bord / modules disponibles |
| GET | `/api/scans/{id}/results` · `/graph` | Résultats / graphe de relations |
| DELETE | `/api/scans/{id}` | Suppression |
| POST/DELETE | `/api/scans/{id}/tags` · `/tags/{tag}` | Ajout / suppression d'un tag |
| POST | `/api/scans/{id}/favorite` | Ajoute ou retire des favoris |
| POST/DELETE | `/api/scans/{id}/notes` · `/notes/{note_id}` | Ajout / suppression d'une note |
| GET | `/api/compare/{id1}/{id2}` | Différences entre deux scans |
| GET | `/api/reports/{id}?format=…` | json/html/md/pdf/csv/stix/misp |
| GET/PUT/DELETE | `/api/settings/api-keys` · `/api-keys/{service}` | Gestion des clés API enregistrées (appliquées immédiatement) |
| GET | `/api/settings/modules` | Disponibilité des modules avec les clés actuelles |
| POST · GET | `/api/auth/login` · `/api/auth/me` | Connexion JWT / utilisateur courant |
| WS | `/ws/scan/{id}` | Événements en direct : `scan_start`, `module_*`, `scan_complete`, `scan_error` |

`GET /api/scans` accepte les filtres `target`, `tag` et `favorite=true`.

## Configuration

Tous les réglages viennent de variables d'environnement (préfixe `RECONKIT_`) et/ou du
fichier `.env` (voir `.env.example`). Les principaux : `RECONKIT_DATABASE_URL`,
`RECONKIT_SECRET_KEY`, `RECONKIT_CACHE_BACKEND` (`disk` | `redis` | `none`),
`RECONKIT_MAX_CONCURRENCY`, `RECONKIT_DEFAULT_TIMEOUT`. Un fichier `reconkit.yml` peut aussi
fournir des valeurs de base.

Les clés API utilisent des noms sans préfixe : `SHODAN_API_KEY`, `VIRUSTOTAL_API_KEY`,
`ABUSEIPDB_API_KEY`, `HUNTER_API_KEY`, `OTX_API_KEY`, `GITHUB_TOKEN`,
`GOOGLE_CSE_API_KEY` + `GOOGLE_CSE_ID`, `IPINFO_TOKEN`, `HIBP_API_KEY`. Elles peuvent aussi
être enregistrées (chiffrées) depuis la page **Réglages** et sont alors actives
immédiatement.

**Authentification** : l'API est ouverte par défaut (usage local, un seul utilisateur).
Mets `RECONKIT_REQUIRE_AUTH=true` pour activer la connexion JWT ; le premier compte est créé
à partir de `RECONKIT_ADMIN_USER` / `RECONKIT_ADMIN_PASSWORD`. Change-les, et définis une
`RECONKIT_SECRET_KEY` longue et aléatoire.

## Ajouter un module

1. Crée `reconkit/modules/mon_module.py` avec une classe qui hérite de `BaseModule`
   (définis `name`, `description`, `supported_types`, `category` ; implémente
   `async run()` qui renvoie `self.ok(...)`, `self.failed(...)` ou `self.skipped(...)`).
2. Importe-le dans `reconkit/modules/__init__.py` et ajoute son nom à `TYPE_MODULES` dans
   `reconkit/engine.py`.
3. Donne-lui un libellé français et une fiche de résultat dans `web/src/lib/modules.ts` et
   `web/src/components/Findings.tsx`.
4. Ajoute un test avec HTTP simulé (`respx`) dans `tests/test_modules/`.

## Tests

```bash
pytest                       # hermétiques : HTTP simulé + faux module hors ligne (28 tests)
cd web && npx tsc --noEmit   # vérification des types du frontend
```

## Légal et éthique

ReconKit sert aux audits de sécurité autorisés, à la recherche et à l'apprentissage. Tu es
responsable de t'assurer que tu as le droit de collecter des informations sur chaque cible.
L'outil est passif par conception, mais collecter et stocker des données personnelles
(emails, profils, fuites) reste encadré par la loi (RGPD notamment). N'analyse que des
cibles qui t'appartiennent ou que tu es autorisé à évaluer.

## Licence

MIT
