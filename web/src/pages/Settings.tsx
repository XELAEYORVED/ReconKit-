import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, useModules } from "../lib/api";

const SERVICE_LABELS: Record<string, string> = {
  shodan: "Shodan",
  virustotal: "VirusTotal",
  abuseipdb: "AbuseIPDB",
  hunter: "Hunter.io",
  otx: "AlienVault OTX",
  github: "GitHub Token",
  google_cse: "Google CSE",
  ipinfo: "ipinfo.io",
  hibp: "Have I Been Pwned",
};

export function Settings() {
  const qc = useQueryClient();
  const { data: keys } = useQuery({ queryKey: ["apiKeys"], queryFn: api.apiKeys });
  const { data: modules } = useModules();
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);

  const save = async (service: string) => {
    if (!draft[service]) return;
    setSaving(service);
    await api.setApiKey(service, draft[service]);
    setDraft((d) => ({ ...d, [service]: "" }));
    await qc.invalidateQueries({ queryKey: ["apiKeys"] });
    await qc.invalidateQueries({ queryKey: ["modules"] });
    setSaving(null);
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-xl text-neon">Settings</h1>

      <div className="card">
        <h3 className="text-sm text-neon mb-1">API Keys</h3>
        <p className="text-xs text-gray-500 mb-4">
          Keys are stored encrypted. ReconKit works without them — keys simply unlock advanced
          modules.
        </p>
        <div className="space-y-2">
          {(keys ?? []).map((k) => (
            <div key={k.service} className="flex items-center gap-2">
              <div className="w-40 text-sm text-gray-300">{SERVICE_LABELS[k.service] ?? k.service}</div>
              <input
                type="password"
                className="input flex-1"
                placeholder={k.configured ? `configured (${k.source})` : "not set"}
                value={draft[k.service] ?? ""}
                onChange={(e) => setDraft((d) => ({ ...d, [k.service]: e.target.value }))}
              />
              <button className="btn btn-ghost" disabled={saving === k.service} onClick={() => save(k.service)}>
                Save
              </button>
              {k.configured && k.source === "database" && (
                <button
                  className="btn btn-ghost text-risk-high"
                  onClick={async () => {
                    await api.deleteApiKey(k.service);
                    qc.invalidateQueries({ queryKey: ["apiKeys"] });
                    qc.invalidateQueries({ queryKey: ["modules"] });
                  }}
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3 className="text-sm text-neon mb-3">Module availability</h3>
        <div className="grid sm:grid-cols-2 gap-2">
          {(modules ?? []).map((m) => (
            <div key={m.name} className="flex items-center justify-between text-xs py-1 px-2 rounded bg-panel2/50">
              <span className="font-mono text-gray-300">{m.name}</span>
              <span className={m.available ? "text-neon" : "text-risk-high"}>
                {m.available ? "ready" : m.requires_api_key ? "needs key" : "unavailable"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
