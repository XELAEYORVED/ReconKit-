import { useScanStore } from "../stores/scanStore";

const ICON: Record<string, string> = {
  pending: "○",
  running: "◐",
  ok: "●",
  skipped: "◌",
  error: "✕",
};
const COLOR: Record<string, string> = {
  pending: "text-gray-600",
  running: "text-cyan animate-pulse",
  ok: "text-neon",
  skipped: "text-yellow-500",
  error: "text-risk-high",
};

export function ScanProgress() {
  const { modules, progress, finished } = useScanStore();
  const list = Object.values(modules);
  const pct = Math.round(progress * 100);

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-300">
          {finished ? "Scan complete" : "Scanning…"}
        </span>
        <span className="text-xs text-gray-500 font-mono">{pct}%</span>
      </div>
      <div className="h-2 bg-panel2 rounded-full overflow-hidden">
        <div
          className="h-full bg-neon shadow-neon transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 mt-2">
        {list.map((m) => (
          <div
            key={m.name}
            className="flex items-center gap-2 text-xs py-1 px-2 rounded bg-panel2/50"
          >
            <span className={COLOR[m.status]}>{ICON[m.status]}</span>
            <span className="font-mono text-gray-300">{m.name}</span>
            {m.status === "error" && (
              <span className="text-risk-high truncate text-[10px]">{m.error}</span>
            )}
            {m.status === "skipped" && (
              <span className="text-yellow-600 truncate text-[10px]">skipped</span>
            )}
          </div>
        ))}
        {list.length === 0 && <div className="text-xs text-gray-500">Waiting for modules…</div>}
      </div>
    </div>
  );
}
