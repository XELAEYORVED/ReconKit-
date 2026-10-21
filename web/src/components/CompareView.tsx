import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";

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
      <h1 className="text-xl text-neon">Compare Scans</h1>
      {!ids && (
        <div className="card flex gap-2">
          <input className="input font-mono" placeholder="scan-id A" value={a} onChange={(e) => setA(e.target.value)} />
          <input className="input font-mono" placeholder="scan-id B" value={b} onChange={(e) => setB(e.target.value)} />
        </div>
      )}
      {isLoading && <div className="text-gray-500">Comparing…</div>}
      {error && <div className="text-risk-high text-sm">{(error as Error).message}</div>}
      {data && (
        <>
          <div className="card flex items-center justify-around text-center">
            <div>
              <div className="text-xs text-gray-500">{data.scan_before.id}</div>
              <div className="text-2xl font-mono">{data.threat_score.before}</div>
            </div>
            <div className="text-3xl text-gray-600">→</div>
            <div>
              <div className="text-xs text-gray-500">{data.scan_after.id}</div>
              <div className="text-2xl font-mono">{data.threat_score.after}</div>
            </div>
            <div
              className={`text-2xl font-mono ${
                data.threat_score.delta > 0 ? "text-risk-high" : data.threat_score.delta < 0 ? "text-risk-low" : "text-gray-500"
              }`}
            >
              {data.threat_score.delta > 0 ? "+" : ""}
              {data.threat_score.delta}
            </div>
          </div>

          {Object.entries<any>(data.changes).map(([key, change]) => (
            <div key={key} className="card">
              <h3 className="text-sm text-neon mb-2 capitalize">{key.replace("_", " ")}</h3>
              <div className="grid sm:grid-cols-2 gap-4 text-xs font-mono">
                <div>
                  <div className="text-risk-low mb-1">Added ({change.added.length})</div>
                  {change.added.map((x: string) => (
                    <div key={x} className="text-green-400">+ {x}</div>
                  ))}
                </div>
                <div>
                  <div className="text-risk-high mb-1">Removed ({change.removed.length})</div>
                  {change.removed.map((x: string) => (
                    <div key={x} className="text-red-400">- {x}</div>
                  ))}
                </div>
              </div>
            </div>
          ))}
          {Object.keys(data.changes).length === 0 && (
            <div className="card text-sm text-gray-500">No differences detected between these scans.</div>
          )}
        </>
      )}
    </div>
  );
}
