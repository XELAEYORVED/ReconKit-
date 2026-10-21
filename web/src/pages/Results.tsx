import { useState } from "react";
import { useParams } from "react-router-dom";
import { DomainTimeline } from "../components/DomainTimeline";
import { ExportPanel } from "../components/ExportPanel";
import { GeoMap } from "../components/GeoMap";
import { NetworkMap } from "../components/NetworkMap";
import { RelationGraph } from "../components/RelationGraph";
import { ResultsTable } from "../components/ResultsTable";
import { ThreatScore } from "../components/ThreatScore";
import { useScan } from "../lib/api";
import type { ResultItem } from "../lib/types";

const TABS = [
  "Synthèse",
  "Infrastructure",
  "Technologies",
  "Identité",
  "Historique",
  "Carte",
  "Graphe",
  "Brut",
] as const;
type Tab = (typeof TABS)[number];

function pick(results: ResultItem[], names: string[]) {
  return results.filter((r) => names.includes(r.module_name));
}

export function Results() {
  const { id } = useParams();
  const { data: scan, isLoading } = useScan(id, false);
  const [tab, setTab] = useState<Tab>("Synthèse");

  if (isLoading || !scan) return <div className="text-gray-500">Loading results…</div>;
  const results = scan.results ?? [];
  const summary = scan.summary;
  const graph = summary?.graph ?? { nodes: [], edges: [] };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-xl text-neon font-mono">{scan.target}</h1>
          <div className="text-xs text-gray-500">
            {scan.target_type} · {scan.id} · {scan.status}
          </div>
        </div>
      </div>

      <div className="flex gap-1 flex-wrap border-b border-border">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm border-b-2 -mb-px transition-colors ${
              tab === t ? "border-neon text-neon" : "border-transparent text-gray-400 hover:text-cyan"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Synthèse" && (
        <div className="grid md:grid-cols-3 gap-5">
          <div className="card flex flex-col items-center justify-center">
            <ThreatScore score={scan.threat_score} />
          </div>
          <div className="card md:col-span-2">
            <h3 className="text-sm text-neon mb-2">Threat factors</h3>
            {(summary?.threat_factors ?? []).length === 0 && (
              <div className="text-sm text-gray-500">No risk factors detected.</div>
            )}
            <ul className="space-y-1 text-sm">
              {summary?.threat_factors?.map((f, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-risk-high font-mono">+{f.points}</span>
                  <span className="text-gray-300">{f.reason}</span>
                </li>
              ))}
            </ul>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-4 text-xs">
              {Object.entries(summary?.highlights ?? {}).map(([k, v]) => (
                <div key={k} className="bg-panel2 rounded-lg p-2">
                  <div className="text-gray-500">{k.replace(/_/g, " ")}</div>
                  <div className="text-gray-200 font-mono truncate">
                    {Array.isArray(v) ? v.length : String(v ?? "—")}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="md:col-span-3">
            <ExportPanel scanId={scan.id} />
          </div>
        </div>
      )}

      {tab === "Infrastructure" && (
        <div className="space-y-4">
          <ResultsTable results={pick(results, ["whois", "dns", "subdomains", "cert_transparency", "ip_geo", "network_map"])} />
        </div>
      )}

      {tab === "Technologies" && (
        <ResultsTable results={pick(results, ["tech", "headers", "shodan"])} />
      )}

      {tab === "Identité" && (
        <ResultsTable results={pick(results, ["email", "social", "leak_check", "github", "metadata", "pastebin", "google_dork"])} />
      )}

      {tab === "Historique" && <DomainTimeline results={results} />}

      {tab === "Carte" && (
        <div className="space-y-4">
          <GeoMap results={results} />
          <NetworkMap results={results} />
        </div>
      )}

      {tab === "Graphe" && <RelationGraph graph={graph} />}

      {tab === "Brut" && <ResultsTable results={results} />}
    </div>
  );
}
