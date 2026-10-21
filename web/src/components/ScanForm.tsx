import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateScan, useModules } from "../lib/api";
import { detectType } from "../lib/format";
import { useScanStore } from "../stores/scanStore";

export function ScanForm() {
  const [target, setTarget] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [auto, setAuto] = useState(true);
  const { data: modules } = useModules();
  const createScan = useCreateScan();
  const start = useScanStore((s) => s.start);
  const navigate = useNavigate();

  const detected = useMemo(() => detectType(target), [target]);

  const applicable = useMemo(
    () => (modules ?? []).filter((m) => detected === "unknown" || m.supported_types.includes(detected as any)),
    [modules, detected],
  );

  const toggle = (name: string) =>
    setSelected((s) => (s.includes(name) ? s.filter((x) => x !== name) : [...s, name]));

  const submit = async () => {
    if (!target.trim()) return;
    const res = await createScan.mutateAsync({
      target: target.trim(),
      modules: auto || selected.length === 0 ? undefined : selected,
    });
    start(res.scan_id);
    navigate(`/scan/${res.scan_id}`);
  };

  return (
    <div className="card space-y-4">
      <div>
        <label className="text-xs text-muted uppercase tracking-widest">Target</label>
        <div className="flex gap-2 mt-1">
          <input
            className="input font-mono"
            placeholder="example.com · 8.8.8.8 · user@example.com · johndoe"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
          />
          <button className="btn btn-primary whitespace-nowrap" disabled={!target.trim() || createScan.isPending} onClick={submit}>
            {createScan.isPending ? "Launching…" : "Run Scan"}
          </button>
        </div>
        {target && (
          <div className="mt-1 text-xs text-muted">
            Detected type:{" "}
            <span className={detected === "unknown" ? "text-risk-high" : "text-accent2"}>{detected}</span>
          </div>
        )}
      </div>

      <label className="flex items-center gap-2 text-sm text-ink/80">
        <input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} />
        Auto-select relevant modules
      </label>

      {!auto && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {applicable.map((m) => (
            <button
              key={m.name}
              onClick={() => toggle(m.name)}
              className={`text-left p-2 rounded-lg border text-xs transition-colors ${
                selected.includes(m.name)
                  ? "border-accent bg-panel2 text-accent"
                  : "border-border text-muted hover:border-accent2"
              } ${!m.available ? "opacity-50" : ""}`}
              title={m.description}
            >
              <div className="font-semibold flex items-center justify-between">
                {m.name}
                {m.requires_api_key && !m.available && <span className="text-[9px] text-risk-high">key</span>}
              </div>
              <div className="text-[10px] text-muted truncate">{m.description}</div>
            </button>
          ))}
        </div>
      )}
      {createScan.isError && (
        <div className="text-risk-high text-xs">{(createScan.error as Error).message}</div>
      )}
    </div>
  );
}
