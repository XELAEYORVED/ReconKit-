import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { DomainTimeline } from "../components/DomainTimeline";
import { ExportPanel } from "../components/ExportPanel";
import { Findings } from "../components/Findings";
import { GeoMap } from "../components/GeoMap";
import { Icon, type IconName } from "../components/Icon";
import { NetworkMap } from "../components/NetworkMap";
import { RelationGraph } from "../components/RelationGraph";
import { ResultsTable } from "../components/ResultsTable";
import { ThreatScore } from "../components/ThreatScore";
import { useScan } from "../lib/api";
import { factorFr, riskFromScore } from "../lib/format";
import { TYPE_LABEL } from "../lib/modules";

const TABS: { id: string; label: string; icon: IconName }[] = [
  { id: "bilan", label: "Bilan", icon: "shield" },
  { id: "timeline", label: "Chronologie", icon: "clock" },
  { id: "map", label: "Carte & réseau", icon: "map" },
  { id: "graph", label: "Graphe", icon: "graph" },
  { id: "raw", label: "Données brutes", icon: "code" },
];

const VERDICT: Record<string, string> = {
  low: "Rien d'inquiétant dans les sources publiques consultées.",
  medium: "Quelques points à corriger, rien d'urgent.",
  high: "Plusieurs problèmes sérieux sont visibles publiquement.",
  critical: "Exposition importante : à traiter en priorité.",
};

export function Results() {
  const { id } = useParams();
  const { data: scan, isLoading } = useScan(id, false);
  const [tab, setTab] = useState("bilan");

  if (isLoading || !scan) return <div className="text-muted">Chargement des résultats…</div>;
  const results = scan.results ?? [];
  const summary = scan.summary;
  const graph = summary?.graph ?? { nodes: [], edges: [] };
  const factors = summary?.threat_factors ?? [];
  const okCount = results.filter((r) => r.status === "ok").length;
  const skipped = results.filter((r) => r.status === "skipped").length;
  const errors = results.filter((r) => r.status === "error").length;
  const level = riskFromScore(scan.threat_score);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="min-w-0">
          <Link to="/history" className="text-[13px] text-accent hover:underline">← Historique</Link>
          <h1 className="text-[28px] md:text-[34px] leading-tight mt-1 break-all">{scan.target}</h1>
          <div className="flex items-center gap-2 text-[13px] text-muted mt-1 flex-wrap">
            <span className="bg-panel rounded-full px-2.5 py-0.5 border border-border/60 text-ink/80">
              {TYPE_LABEL[scan.target_type] ?? scan.target_type}
            </span>
            {scan.started_at && <span>{new Date(scan.started_at).toLocaleString("fr-FR")}</span>}
            <span className="font-mono text-xs">{scan.id}</span>
          </div>
        </div>
        <Link to="/scan" className="btn btn-ghost inline-flex items-center gap-1.5">
          <Icon name="scan" size={15} /> Nouveau scan
        </Link>
      </div>

      <div className="flex gap-1 overflow-x-auto bg-panel2 border border-border/60 rounded-full p-1 w-fit max-w-full">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[13px] font-medium whitespace-nowrap transition-colors ${
              tab === t.id ? "bg-white text-ink shadow-card" : "text-muted hover:text-ink"
            }`}
          >
            <Icon name={t.icon} size={14} />
            {t.label}
          </button>
        ))}
      </div>

      {tab === "bilan" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card flex flex-col items-center justify-center text-center gap-3 !py-6">
              <ThreatScore score={scan.threat_score} />
              <p className="text-sm text-ink/80 max-w-[240px]">{VERDICT[level]}</p>
            </div>
            <div className="card md:col-span-2">
              <h3 className="font-semibold text-ink">Pourquoi ce score ?</h3>
              <p className="text-xs text-muted mt-0.5 mb-3">
                Chaque problème trouvé ajoute des points (sur 100). Plus le score est haut, plus la cible est exposée.
              </p>
              {factors.length === 0 ? (
                <div className="flex items-center gap-2 text-sm text-[#1f7a35] bg-risk-low/10 rounded-xl px-3 py-2">
                  <Icon name="check" size={16} /> Aucun problème détecté.
                </div>
              ) : (
                <ul className="space-y-1.5">
                  {factors.map((f, i) => (
                    <li key={i} className="flex items-center gap-3 text-sm">
                      <span className="w-11 text-center shrink-0 rounded-full bg-risk-high/10 text-[#b35c00] text-xs font-semibold py-0.5 tabular-nums">
                        +{f.points}
                      </span>
                      <span className="text-ink/85">{factorFr(f.reason)}</span>
                    </li>
                  ))}
                </ul>
              )}
              <div className="grid grid-cols-3 gap-2 mt-5">
                <Count n={okCount} label="modules avec résultats" color="#34c759" />
                <Count n={skipped} label="ignorés (clé API)" color="#8e8e93" />
                <Count n={errors} label="en erreur" color="#ff3b30" />
              </div>
            </div>
          </div>

          {okCount === 0 && (
            <div className="card flex items-start gap-3 bg-risk-medium/5 border-risk-medium/30">
              <span className="text-[#9a5b00] mt-0.5"><Icon name="info" /></span>
              <div className="text-sm text-ink/85">
                <div className="font-medium">Aucune information trouvée pour cette cible.</div>
                {skipped > 0
                  ? <>Les modules qui s'appliquent ici demandent une clé API. Ajoute-en dans <Link to="/settings" className="text-accent underline">Réglages</Link>, ou scanne plutôt un nom de domaine, qui marche sans clé.</>
                  : <>Vérifie l'orthographe de la cible ou réessaie plus tard (certaines sources publiques sont parfois indisponibles).</>}
              </div>
            </div>
          )}

          <Findings results={results} />
          <ExportPanel scanId={scan.id} />
        </div>
      )}

      {tab === "timeline" && <DomainTimeline results={results} />}

      {tab === "map" && (
        <div className="space-y-4">
          <GeoMap results={results} />
          <NetworkMap results={results} />
        </div>
      )}

      {tab === "graph" && <RelationGraph graph={graph} />}

      {tab === "raw" && <ResultsTable results={results} />}
    </div>
  );
}

function Count({ n, label, color }: { n: number; label: string; color: string }) {
  return (
    <div className="rounded-xl bg-panel2 px-3 py-2">
      <div className="text-xl font-semibold tabular-nums" style={{ color }}>{n}</div>
      <div className="text-[11px] text-muted leading-tight">{label}</div>
    </div>
  );
}
