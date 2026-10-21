import { useMemo, useState } from "react";
import type { ResultItem } from "../lib/types";

export function ResultsTable({ results }: { results: ResultItem[] }) {
  const [q, setQ] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const needle = q.toLowerCase();
    return results.filter(
      (r) =>
        !needle ||
        r.module_name.includes(needle) ||
        JSON.stringify(r.data).toLowerCase().includes(needle),
    );
  }, [results, q]);

  return (
    <div className="card">
      <input
        className="input mb-3"
        placeholder="Filter results (module, value…)"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-muted border-b border-border">
              <th className="py-2 px-2">Module</th>
              <th className="px-2">Status</th>
              <th className="px-2">Confidence</th>
              <th className="px-2">Tags</th>
              <th className="px-2">Summary</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => (
              <>
                <tr
                  key={r.id}
                  className="border-b border-border/50 hover:bg-panel2/50 cursor-pointer"
                  onClick={() => setExpanded(expanded === r.id ? null : r.id)}
                >
                  <td className="py-2 px-2 font-mono text-accent2">{r.module_name}</td>
                  <td className="px-2">
                    <span
                      className={
                        r.status === "ok"
                          ? "text-accent"
                          : r.status === "skipped"
                            ? "text-risk-medium"
                            : "text-risk-high"
                      }
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="px-2 text-muted">{Math.round(r.confidence * 100)}%</td>
                  <td className="px-2">
                    {r.tags.slice(0, 3).map((t) => (
                      <span key={t} className="tag">
                        {t}
                      </span>
                    ))}
                  </td>
                  <td className="px-2 text-muted">
                    {r.status === "ok" ? `${Object.keys(r.data).length} fields` : r.error}
                  </td>
                </tr>
                {expanded === r.id && (
                  <tr key={r.id + "-exp"}>
                    <td colSpan={5} className="bg-base p-0">
                      <pre className="p-3 text-[10px] text-ink/80 overflow-x-auto max-h-96">
                        {JSON.stringify(r.data, null, 2)}
                      </pre>
                    </td>
                  </tr>
                )}
              </>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="py-4 text-center text-muted">
                  No matching results.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
