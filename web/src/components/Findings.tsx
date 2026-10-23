import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { GROUPS, MODULES, moduleLabel } from "../lib/modules";
import type { ResultItem } from "../lib/types";
import { Icon } from "./Icon";

type Tone = "good" | "warn" | "bad" | "info";
interface Described {
  facts: [string, ReactNode][];
  chips?: { title: string; items: string[]; tone?: Tone };
  links?: { title: string; items: { label: string; url: string }[] };
  verdict?: { tone: Tone; text: string };
}

const yes = (v: unknown) => (v ? "Oui" : "Non");
const n = (v: unknown) => (typeof v === "number" ? v.toLocaleString("fr-FR") : String(v ?? "—"));

function fmtDate(v: unknown): string {
  if (!v) return "—";
  const s = String(Array.isArray(v) ? v[0] : v);
  if (/^\d{14}$/.test(s)) return `${s.slice(6, 8)}/${s.slice(4, 6)}/${s.slice(0, 4)}`; // wayback
  const d = new Date(s);
  return isNaN(d.getTime()) ? s.slice(0, 10) : d.toLocaleDateString("fr-FR");
}
const list = (v: unknown): string[] =>
  Array.isArray(v) ? v.map(String) : v ? [String(v)] : [];

const PROVIDER: Record<string, string> = {
  free_webmail: "Messagerie gratuite (Gmail, Outlook…)",
  disposable: "Adresse jetable",
  custom_domain: "Domaine propre (entreprise, perso)",
};

function describe(r: ResultItem): Described {
  const d = r.data ?? {};
  switch (r.module_name) {
    case "whois":
      return {
        facts: [
          ["Registrar", d.registrar ?? "—"],
          ["Créé le", fmtDate(d.created)],
          ["Expire le", fmtDate(d.expires)],
          ["Organisation", d.org ?? "—"],
          ["Pays", d.country ?? "—"],
        ],
        chips: { title: "Serveurs DNS", items: list(d.name_servers).map((s) => s.toLowerCase()) },
      };
    case "dns": {
      const nullMx = (d.records?.MX ?? []).every((m: string) => m.trim() === "0 .");
      return {
        facts: [
          ["Adresses IPv4", (d.ipv4 ?? []).length],
          ["Adresses IPv6", (d.ipv6 ?? []).length],
          ["Reçoit des emails", d.has_mx && !nullMx ? "Oui" : "Non"],
          ["SPF", d.spf?.length ? "Présent" : "Absent"],
          ["DMARC", d.dmarc?.length ? "Présent" : "Absent"],
        ],
        chips: { title: "Adresses IP", items: [...(d.ipv4 ?? []), ...(d.ipv6 ?? [])] },
        verdict:
          d.dmarc?.length
            ? { tone: "good", text: "Le domaine est protégé contre l'usurpation d'email (DMARC)." }
            : { tone: "warn", text: "Pas de DMARC : quelqu'un pourrait envoyer de faux emails au nom de ce domaine." },
      };
    }
    case "subdomains":
      return {
        facts: [
          ["Sous-domaines trouvés", n(d.count)],
          ["Actifs (répondent)", n(d.live_count)],
        ],
        chips: { title: "Exemples", items: (d.subdomains ?? []).slice(0, 24) },
      };
    case "cert_transparency":
      return {
        facts: [
          ["Certificats uniques", n(d.unique_certificates)],
          ["Noms couverts", n(d.san_count)],
        ],
        chips: { title: "Émetteurs", items: Object.keys(d.issuers ?? {}).slice(0, 6).map((i) => i.replace(/^.*O=/, "").split(",")[0].replace(/"/g, "").trim()) },
      };
    case "ip_geo":
      return {
        facts: [
          ["Adresse IP", <span className="font-mono">{d.ip}</span>],
          ["Lieu", [d.city, d.region, d.country].filter(Boolean).join(", ") || "—"],
          ["Hébergeur", d.org ?? d.isp ?? "—"],
          ["Réseau", d.asn ? `${d.asn}${d.as_name ? " · " + d.as_name : ""}` : "—"],
          ["Nom inverse", d.reverse_dns ?? "—"],
        ],
      };
    case "network_map": {
      const a = d.asn ?? {};
      return {
        facts: [
          ["Réseau", a.asn ? `AS${a.asn}` : "—"],
          ["Opérateur", a.name ?? "—"],
          ["Organisation", a.description ?? "—"],
          ["Pays", a.country ?? "—"],
          ["Plages d'IP annoncées", n(d.prefix_count)],
          ["Fournisseurs amont", n(d.peers?.counts?.left ?? d.peers?.upstreams?.length)],
        ],
      };
    }
    case "tech":
      return {
        facts: [
          ["Serveur", d.server ?? "—"],
          ["Propulsé par", d.powered_by ?? "—"],
        ],
        chips: { title: "Technologies détectées", items: d.all ?? [] },
        verdict: (d.all ?? []).length === 0 ? { tone: "info", text: "Aucune technologie reconnue sur la page d'accueil." } : undefined,
      };
    case "headers": {
      const grade = d.grade ?? "?";
      const tone: Tone = ["A", "B"].includes(grade) ? "good" : grade === "C" ? "warn" : "bad";
      return {
        facts: [
          ["Note", <span className="text-lg font-semibold">{grade} <span className="text-muted text-sm font-normal">({d.score}/100)</span></span>],
          ["Protections présentes", Object.keys(d.present ?? {}).length],
          ["Protections manquantes", (d.missing ?? []).length],
          ["CORS ouvert à tous", yes(d.cors_wildcard)],
        ],
        chips: { title: "Manquantes", items: d.missing ?? [], tone: "warn" },
        verdict: {
          tone,
          text:
            tone === "good"
              ? "Le site envoie la plupart des protections recommandées."
              : "Le site n'envoie pas plusieurs protections de base au navigateur.",
        },
      };
    }
    case "shodan": {
      const vulns = d.vulns ?? [];
      return {
        facts: [
          ["Ports ouverts", (d.ports ?? []).length],
          ["Failles connues (CVE)", vulns.length],
          ["Source", d.source === "shodan-api" ? "Shodan" : "Shodan InternetDB (gratuit)"],
        ],
        chips: vulns.length
          ? { title: "Failles connues", items: vulns.slice(0, 20), tone: "bad" }
          : { title: "Ports", items: (d.ports ?? []).map(String) },
        verdict: vulns.length
          ? { tone: "bad", text: `${vulns.length} faille(s) connue(s) signalée(s) sur ce serveur.` }
          : { tone: "good", text: "Aucune faille connue signalée." },
      };
    }
    case "reputation":
      return {
        facts: [
          ["Signaux négatifs", n(d.malicious_signals)],
          ["Sources consultées", (d.providers_used ?? []).join(", ") || "—"],
        ],
        verdict: d.malicious_signals
          ? { tone: "bad", text: "Cette adresse est signalée par au moins une source." }
          : { tone: "good", text: "Aucun signalement trouvé." },
      };
    case "email":
      return {
        facts: [
          ["Emails trouvés", n(d.email_count)],
          ["Format probable", d.pattern ?? "—"],
          ["Organisation", d.organization ?? "—"],
        ],
        chips: { title: "Adresses", items: d.emails ?? [] },
        verdict: !d.hunter_enabled ? { tone: "info", text: "Ajoute une clé Hunter.io pour trouver beaucoup plus d'adresses." } : undefined,
      };
    case "email_profile": {
      const g = d.gravatar ?? {};
      return {
        facts: [
          ["Domaine", d.domain],
          ["Type de fournisseur", PROVIDER[d.provider_type] ?? d.provider_type],
          ["Peut recevoir des emails", yes(d.can_receive_mail)],
          ["SPF", d.spf?.length ? "Présent" : "Absent"],
          ["DMARC", d.dmarc_policy ? `Présent (politique « ${d.dmarc_policy} »)` : "Absent"],
          ["Profil Gravatar public", g.exists ? g.display_name || g.username || "Oui" : "Non"],
        ],
        links: g.exists
          ? {
              title: "Profil public",
              items: [
                ...(g.profile_url ? [{ label: "Profil Gravatar", url: g.profile_url }] : []),
                ...(g.accounts ?? []).filter((a: any) => a.url).map((a: any) => ({ label: a.site ?? a.url, url: a.url })),
              ],
            }
          : undefined,
        verdict: !d.can_receive_mail
          ? { tone: "bad", text: "Ce domaine ne peut pas recevoir d'emails : l'adresse est probablement fausse." }
          : d.provider_type === "disposable"
            ? { tone: "warn", text: "Adresse jetable : souvent utilisée pour rester anonyme." }
            : { tone: "good", text: "Adresse valide côté domaine." },
      };
    }
    case "leak_check":
      return {
        facts: [["Fuites trouvées", n(d.breach_count)]],
        chips: { title: "Fuites", items: (d.breaches ?? []).map((b: any) => `${b.name} (${fmtDate(b.breach_date)})`), tone: "bad" },
        verdict: d.breached
          ? { tone: "bad", text: "Cet email apparaît dans des fuites : change les mots de passe concernés." }
          : { tone: "good", text: "Aucune fuite connue pour cet email." },
      };
    case "social": {
      const found = Object.entries<any>(d.found ?? {});
      return {
        facts: [["Profils trouvés", `${d.found_count ?? 0} sur ${d.checked ?? 0} plateformes`]],
        links: { title: "Profils", items: found.map(([site, v]) => ({ label: site, url: v.url })) },
        verdict: { tone: "info", text: "Un pseudo identique ne prouve pas que c'est la même personne." },
      };
    }
    case "github":
      return {
        facts: [
          ["Dépôts qui mentionnent la cible", n(d.repo_mention_count)],
          ["Secrets potentiels", n(d.secret_hit_count)],
        ],
        links: {
          title: "Dépôts",
          items: (d.repo_mentions ?? []).slice(0, 8).map((x: any) => ({ label: x.full_name, url: x.url })),
        },
        verdict: d.note ? { tone: "info", text: "Ajoute un token GitHub pour chercher des secrets dans le code." } : undefined,
      };
    case "metadata":
      return {
        facts: [["Documents publics trouvés", n(d.documents_found)]],
        chips: { title: "Auteurs / logiciels", items: [...(d.authors ?? []), ...(d.software ?? [])] },
      };
    case "wayback":
      return {
        facts: [
          ["Captures archivées", n(d.snapshot_count)],
          ["Première capture", fmtDate(d.first_capture)],
          ["Dernière capture", fmtDate(d.last_capture)],
          ["Pages différentes", n(d.unique_urls)],
        ],
        chips: { title: "Pages sensibles archivées", items: (d.interesting ?? []).slice(0, 15), tone: "warn" },
        verdict: d.note
          ? {
              tone: "info",
              text: d.snapshot_count
                ? "L'archive était surchargée : seule la dernière capture est affichée."
                : "L'archive (Wayback Machine) n'a pas répondu à temps. Réessaie plus tard.",
            }
          : undefined,
      };
    case "google_dork":
    case "pastebin": {
      const items = (d.findings ?? d.hits ?? []) as any[];
      return {
        facts: [["Résultats", items.length]],
        links: { title: "Pages trouvées", items: items.slice(0, 10).map((x) => ({ label: x.title ?? x.url, url: x.url })) },
      };
    }
    default:
      return { facts: [["Champs", Object.keys(d).length]] };
  }
}

const TONE: Record<Tone, string> = {
  good: "bg-risk-low/10 text-[#1f7a35]",
  warn: "bg-risk-medium/10 text-[#9a5b00]",
  bad: "bg-risk-critical/10 text-[#c4271d]",
  info: "bg-accent/10 text-accent2",
};
const TONE_ICON = { good: "check", warn: "alert", bad: "alert", info: "info" } as const;

export function FindingCard({ r }: { r: ResultItem }) {
  const [raw, setRaw] = useState(false);
  const meta = MODULES[r.module_name];

  if (r.status !== "ok") {
    const skipped = r.status === "skipped";
    return (
      <div className="card !p-4 bg-panel/60 flex items-start gap-3">
        <span className={`mt-0.5 ${skipped ? "text-muted" : "text-risk-critical"}`}>
          <Icon name={skipped ? "minus" : "x"} />
        </span>
        <div className="min-w-0">
          <div className="font-medium text-ink/80">{moduleLabel(r.module_name)}</div>
          <div className="text-xs text-muted mt-0.5 break-words">
            {skipped ? (
              <>
                Ignoré : clé API manquante.{" "}
                <Link to="/settings" className="text-accent hover:underline">Ajouter une clé</Link>
              </>
            ) : (
              <>Erreur : {r.error}</>
            )}
          </div>
        </div>
      </div>
    );
  }

  const info = describe(r);
  return (
    <div className="card !p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="font-display font-semibold text-[15px] text-ink">{moduleLabel(r.module_name)}</div>
          {meta && <div className="text-xs text-muted mt-0.5">{meta.plain}</div>}
        </div>
        <button
          className="text-muted hover:text-accent shrink-0"
          onClick={() => setRaw((x) => !x)}
          title="Voir les données brutes"
        >
          <Icon name="code" size={16} />
        </button>
      </div>

      {info.verdict && (
        <div className={`flex items-start gap-2 text-[13px] rounded-xl px-3 py-2 ${TONE[info.verdict.tone]}`}>
          <Icon name={TONE_ICON[info.verdict.tone]} size={16} className="mt-px" />
          <span>{info.verdict.text}</span>
        </div>
      )}

      <dl className="grid grid-cols-1 gap-x-4 gap-y-1.5 text-[13px]">
        {info.facts.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-3 border-b border-border/40 pb-1.5 last:border-0">
            <dt className="text-muted">{k}</dt>
            <dd className="text-ink text-right min-w-0 break-words">{v ?? "—"}</dd>
          </div>
        ))}
      </dl>

      {info.chips && info.chips.items.length > 0 && (
        <div>
          <div className="text-[11px] uppercase tracking-wider text-muted mb-1.5">{info.chips.title}</div>
          <div className="flex flex-wrap gap-1">
            {info.chips.items.map((c) => (
              <span
                key={c}
                className={`text-xs rounded-full px-2.5 py-0.5 font-mono ${
                  info.chips!.tone ? TONE[info.chips!.tone] : "bg-panel2 text-ink/80 border border-border/60"
                }`}
              >
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      {info.links && info.links.items.length > 0 && (
        <div>
          <div className="text-[11px] uppercase tracking-wider text-muted mb-1.5">{info.links.title}</div>
          <div className="flex flex-col gap-1">
            {info.links.items.map((l) => (
              <a
                key={l.url}
                href={l.url}
                target="_blank"
                rel="noreferrer noopener"
                className="text-[13px] text-accent2 hover:text-accent inline-flex items-center gap-1.5 truncate"
              >
                <Icon name="external" size={13} />
                <span className="truncate">{l.label}</span>
              </a>
            ))}
          </div>
        </div>
      )}

      {raw && (
        <pre className="text-[10px] bg-panel2 rounded-xl p-3 overflow-auto max-h-72 text-ink/80">
          {JSON.stringify(r.data, null, 2)}
        </pre>
      )}
    </div>
  );
}

/** All results, grouped by theme; successful modules first, then skipped/errors. */
export function Findings({ results }: { results: ResultItem[] }) {
  const ok = results.filter((r) => r.status === "ok");
  const other = results.filter((r) => r.status !== "ok");
  const groups = Object.entries(GROUPS)
    .map(([g, label]) => ({ label, items: ok.filter((r) => (MODULES[r.module_name]?.group ?? "infra") === g) }))
    .filter((g) => g.items.length);

  return (
    <div className="space-y-8">
      {groups.map((g) => (
        <section key={g.label}>
          <h2 className="text-[13px] uppercase tracking-wider text-muted font-semibold mb-3">{g.label}</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {g.items.map((r) => (
              <FindingCard key={r.id ?? r.module_name} r={r} />
            ))}
          </div>
        </section>
      ))}
      {other.length > 0 && (
        <section>
          <h2 className="text-[13px] uppercase tracking-wider text-muted font-semibold mb-3">
            Non disponibles ({other.length})
          </h2>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
            {other.map((r) => (
              <FindingCard key={r.id ?? r.module_name} r={r} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
