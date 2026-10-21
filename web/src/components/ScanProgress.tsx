import { useScanStore } from "../stores/scanStore";

const ICON: Record<string, string> = {
  pending: "○",
  running: "◐",
  ok: "●",
  skipped: "◌",
  error: "✕",
};
const COLOR: Record<string, string> = {
  pending: "text-muted/70",
  running: "text-accent2 animate-pulse",
  ok: "text-accent",
  skipped: "text-risk-medium",
  error: "text-risk-high",
};

export function ScanProgress() {
  const { modules, progress, finished } = useScanStore();
  const list = Object.values(modules);
  const pct = Math.round(progress * 100);

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm text-ink/80">
          {finished ? "Scan complete" : "Scanning…"}
        </span>
        <span className="text-xs text-muted font-mono">{pct}%</span>
      </div>
      <div className="h-2 bg-panel2 rounded-full overflow-hidden">
        <div
          className="h-full bg-accent shadow-accent transition-all duration-500"
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
            <span className="font-mono text-ink/80">{m.name}</span>
            {m.status === "error" && (
              <span className="text-risk-high truncate text-[10px]">{m.error}</span>
            )}
            {m.status === "skipped" && (
              <span className="text-risk-medium truncate text-[10px]">skipped</span>
            )}
          </div>
        ))}
        {list.length === 0 && <div className="text-xs text-muted">Waiting for modules…</div>}
      </div>
    </div>
  );
}
