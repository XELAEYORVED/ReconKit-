import { moduleLabel } from "../lib/modules";
import { useScanStore } from "../stores/scanStore";
import { Icon } from "./Icon";

const STATE: Record<string, { label: string; cls: string }> = {
  pending: { label: "en attente", cls: "text-muted" },
  running: { label: "en cours…", cls: "text-accent" },
  ok: { label: "trouvé", cls: "text-[#1f7a35]" },
  skipped: { label: "ignoré (clé API)", cls: "text-muted" },
  error: { label: "erreur", cls: "text-[#c4271d]" },
};

function Dot({ status }: { status: string }) {
  if (status === "running")
    return <span className="w-4 h-4 rounded-full border-2 border-accent/30 border-t-accent animate-spin shrink-0" />;
  if (status === "ok") return <span className="text-risk-low"><Icon name="check" size={16} /></span>;
  if (status === "error") return <span className="text-risk-critical"><Icon name="x" size={16} /></span>;
  if (status === "skipped") return <span className="text-muted"><Icon name="minus" size={16} /></span>;
  return <span className="w-4 h-4 rounded-full border-2 border-border shrink-0" />;
}

export function ScanProgress() {
  const { modules, progress, finished, error } = useScanStore();
  const list = Object.values(modules);
  const pct = Math.round(progress * 100);

  if (error) {
    return (
      <div className="card flex items-start gap-3 border-risk-critical/30">
        <span className="text-risk-critical mt-0.5"><Icon name="alert" /></span>
        <div>
          <div className="font-medium text-ink">Le scan a échoué</div>
          <div className="text-sm text-muted mt-0.5">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <span className="font-medium text-ink">{finished ? "Scan terminé" : "Analyse en cours…"}</span>
        <span className="text-sm text-muted tabular-nums">{pct} %</span>
      </div>
      <div className="h-1.5 bg-panel2 rounded-full overflow-hidden">
        <div className="h-full bg-accent rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
        {list.map((m) => (
          <div key={m.name} className="flex items-center gap-2.5 text-[13px] py-1.5 border-b border-border/40">
            <Dot status={m.status} />
            <span className="text-ink/85 truncate">{moduleLabel(m.name)}</span>
            <span className={`ml-auto text-xs shrink-0 ${STATE[m.status]?.cls}`} title={m.error}>
              {STATE[m.status]?.label}
            </span>
          </div>
        ))}
        {list.length === 0 && <div className="text-sm text-muted">Démarrage…</div>}
      </div>
    </div>
  );
}
