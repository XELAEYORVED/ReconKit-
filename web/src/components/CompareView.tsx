import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import { PageHeader } from "./Layout";

export function CompareView() {
  const params = useParams();
  const [a, setA] = useState(params.a ?? "");
  const [b, setB] = useState(params.b ?? "");
  const ids = params.a && params.b ? [params.a, params.b] : null;

  const { data, isLoading, error } = useQuery({
    queryKey: ["compare", a, b],
    queryFn: () => api.compare(a, b),
    enabled: !!(a && b),
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Comparer deux scans" subtitle="Ce qui a changé entre deux scans d'une même cible. Astuce : coche deux scans dans l'Historique." />
      {!ids && (
        <div className="card flex flex-col sm:flex-row gap-2">
          <input className="input font-mono" placeholder="ID du 1er scan (scan-…)" value={a} onChange={(e) => setA(e.target.value)} />
          <input className="input font-mono" placeholder="ID du 2e scan (scan-…)" value={b} onChange={(e) => setB(e.target.value)} />
        </div>
      )}
      {isLoading && <div className="text-muted">Comparaison…</div>}
      {error && <div className="text-risk-high text-sm">{(error as Error).message}</div>}
      {data && (
        <>
          <div className="card flex items-center justify-around text-center">
            <div>
              <div className="text-xs text-muted">{data.scan_before.id}</div>
              <div className="text-2xl font-mono">{data.threat_score.before}</div>
            </div>
            <div className="text-3xl text-muted/70">→</div>
            <div>
              <div className="text-xs text-muted">{data.scan_after.id}</div>
              <div className="text-2xl font-mono">{data.threat_score.after}</div>
            </div>
            <div
              className={`text-2xl font-mono ${
                data.threat_score.delta > 0 ? "text-risk-high" : data.threat_score.delta < 0 ? "text-risk-low" : "text-muted"
              }`}
            >
              {data.threat_score.delta > 0 ? "+" : ""}
              {data.threat_score.delta}
            </div>
          </div>

          {Object.entries<any>(data.changes).map(([key, change]) => (
            <div key={key} className="card">
              <h3 className="text-sm text-accent mb-2 capitalize">{key.replace("_", " ")}</h3>
              <div className="grid sm:grid-cols-2 gap-4 text-xs font-mono">
                <div>
                  <div className="text-risk-low mb-1">Ajouté ({change.added.length})</div>
                  {change.added.map((x: string) => (
                    <div key={x} className="text-risk-low">+ {x}</div>
                  ))}
                </div>
                <div>
                  <div className="text-risk-high mb-1">Supprimé ({change.removed.length})</div>
                  {change.removed.map((x: string) => (
                    <div key={x} className="text-risk-critical">- {x}</div>
                  ))}
                </div>
              </div>
            </div>
          ))}
          {Object.keys(data.changes).length === 0 && (
            <div className="card text-sm text-muted">Aucune différence entre ces deux scans.</div>
          )}
        </>
      )}
    </div>
  );
}
