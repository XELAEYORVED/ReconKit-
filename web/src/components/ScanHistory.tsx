import { useState } from "react";
import { Link } from "react-router-dom";
import { useDeleteScan, useScans } from "../lib/api";
import { riskColor, riskFromScore, timeAgo } from "../lib/format";
import { useScanStore } from "../stores/scanStore";

export function ScanHistory() {
  const [q, setQ] = useState("");
  const { data: scans, isLoading } = useScans(q ? `?target=${encodeURIComponent(q)}` : "");
  const del = useDeleteScan();
  const { compareA, compareB, setCompare } = useScanStore();

  const pick = (id: string) => {
    if (compareA === id) setCompare(null, compareB);
    else if (compareB === id) setCompare(compareA, null);
    else if (!compareA) setCompare(id, compareB);
    else if (!compareB) setCompare(compareA, id);
    else setCompare(id, null);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <input className="input" placeholder="Search by target…" value={q} onChange={(e) => setQ(e.target.value)} />
        {compareA && compareB && (
          <Link to={`/compare/${compareA}/${compareB}`} className="btn btn-primary whitespace-nowrap">
            Compare selected →
          </Link>
        )}
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400 border-b border-border text-xs">
              <th className="py-2 px-2">cmp</th>
              <th className="px-2">Target</th>
              <th className="px-2">Type</th>
              <th className="px-2">Status</th>
              <th className="px-2">Score</th>
              <th className="px-2">Started</th>
              <th className="px-2"></th>
            </tr>
          </thead>
          <tbody>
            {(scans ?? []).map((s) => {
              const level = riskFromScore(s.threat_score);
              const checked = compareA === s.id || compareB === s.id;
              return (
                <tr key={s.id} className="border-b border-border/40 hover:bg-panel2/40">
                  <td className="px-2">
                    <input type="checkbox" checked={checked} onChange={() => pick(s.id)} />
                  </td>
                  <td className="px-2 font-mono">
                    <Link to={`/results/${s.id}`} className="text-cyan hover:text-neon">
                      {s.target}
                    </Link>
                  </td>
                  <td className="px-2 text-gray-500 text-xs">{s.target_type}</td>
                  <td className="px-2 text-xs">{s.status}</td>
                  <td className="px-2 font-mono" style={{ color: riskColor(level) }}>
                    {s.threat_score}
                  </td>
                  <td className="px-2 text-gray-500 text-xs">{timeAgo(s.started_at)}</td>
                  <td className="px-2 text-right">
                    <button
                      className="text-gray-600 hover:text-risk-high text-xs"
                      onClick={() => del.mutate(s.id)}
                    >
                      delete
                    </button>
                  </td>
                </tr>
              );
            })}
            {!isLoading && (scans ?? []).length === 0 && (
              <tr>
                <td colSpan={7} className="py-6 text-center text-gray-500">
                  No scans found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
