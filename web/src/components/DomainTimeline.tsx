import type { ResultItem } from "../lib/types";

function parseWb(ts?: string): string {
  if (!ts || ts.length < 8) return "—";
  return `${ts.slice(0, 4)}-${ts.slice(4, 6)}-${ts.slice(6, 8)}`;
}

export function DomainTimeline({ results }: { results: ResultItem[] }) {
  const wb = results.find((r) => r.module_name === "wayback" && r.status === "ok");
  const whois = results.find((r) => r.module_name === "whois" && r.status === "ok");
  const certs = results.find((r) => r.module_name === "cert_transparency" && r.status === "ok");

  const events: { date: string; label: string; kind: string }[] = [];
  if (whois?.data.created) events.push({ date: String(whois.data.created).slice(0, 10), label: "Domaine enregistré", kind: "whois" });
  if (whois?.data.updated) events.push({ date: String(whois.data.updated).slice(0, 10), label: "Informations WHOIS mises à jour", kind: "whois" });
  if (whois?.data.expires) events.push({ date: String(whois.data.expires).slice(0, 10), label: "Expiration de l'enregistrement", kind: "whois" });
  if (wb) {
    events.push({ date: parseWb(wb.data.first_capture), label: "Première capture dans les archives du web", kind: "wayback" });
    events.push({ date: parseWb(wb.data.last_capture), label: `Dernière capture (${wb.data.snapshot_count} au total)`, kind: "wayback" });
  }
  for (const c of (certs?.data.certificates ?? []).slice(0, 6)) {
    if (c.not_before) events.push({ date: String(c.not_before).slice(0, 10), label: `Certificat HTTPS émis par ${c.issuer ?? "?"}`, kind: "cert" });
  }

  const sorted = events.filter((e) => e.date && e.date !== "—").sort((a, b) => a.date.localeCompare(b.date));
  const color: Record<string, string> = { whois: "#0066cc", wayback: "#0071e3", cert: "#ff9f0a" };

  if (sorted.length === 0)
    return <div className="card text-sm text-muted">Pas de données historiques (il faut un scan de domaine).</div>;

  return (
    <div className="card">
      <h3 className="font-semibold text-ink mb-4">Chronologie du domaine</h3>
      <div className="relative pl-6 border-l border-border space-y-4">
        {sorted.map((e, i) => (
          <div key={i} className="relative">
            <span
              className="absolute -left-[26px] top-1 w-3 h-3 rounded-full border-2 border-base"
              style={{ background: color[e.kind] }}
            />
            <div className="text-xs font-mono text-muted">{e.date}</div>
            <div className="text-sm text-ink">{e.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
