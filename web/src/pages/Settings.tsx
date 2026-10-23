import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/Layout";
import { api, useModules } from "../lib/api";
import { moduleLabel } from "../lib/modules";

const SERVICES: Record<string, { label: string; unlocks: string; url: string }> = {
  shodan: { label: "Shodan", unlocks: "Détail des services et bannières (sans clé : version gratuite limitée)", url: "https://account.shodan.io/" },
  virustotal: { label: "VirusTotal", unlocks: "Réputation des domaines et IP", url: "https://www.virustotal.com/gui/my-apikey" },
  abuseipdb: { label: "AbuseIPDB", unlocks: "Signalements d'abus pour une IP", url: "https://www.abuseipdb.com/account/api" },
  otx: { label: "AlienVault OTX", unlocks: "Indicateurs de menace", url: "https://otx.alienvault.com/api" },
  hunter: { label: "Hunter.io", unlocks: "Beaucoup plus d'emails pour un domaine", url: "https://hunter.io/api-keys" },
  hibp: { label: "Have I Been Pwned", unlocks: "Vérifier si un email a fuité (payant)", url: "https://haveibeenpwned.com/API/Key" },
  github: { label: "GitHub (token)", unlocks: "Recherche de secrets dans le code public", url: "https://github.com/settings/tokens" },
  google_cse: { label: "Google CSE", unlocks: "Recherches Google ciblées + sites de paste (il faut aussi GOOGLE_CSE_ID)", url: "https://developers.google.com/custom-search/v1/introduction" },
  ipinfo: { label: "ipinfo.io", unlocks: "Géolocalisation plus précise", url: "https://ipinfo.io/account/token" },
};

export function Settings() {
  const qc = useQueryClient();
  const { data: keys } = useQuery({ queryKey: ["apiKeys"], queryFn: api.apiKeys });
  const { data: modules } = useModules();
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);

  const refresh = async () => {
    await qc.invalidateQueries({ queryKey: ["apiKeys"] });
    await qc.invalidateQueries({ queryKey: ["modules"] });
  };
  const save = async (service: string) => {
    if (!draft[service]) return;
    setSaving(service);
    await api.setApiKey(service, draft[service]);
    setDraft((d) => ({ ...d, [service]: "" }));
    await refresh();
    setSaving(null);
  };

  const ready = (modules ?? []).filter((m) => m.available).length;

  return (
    <div className="max-w-3xl">
      <PageHeader
        title="Réglages"
        subtitle="ReconKit marche sans aucune clé. Les clés API (souvent gratuites) débloquent des modules en plus."
      />
      <div className="space-y-5">
        <div className="card">
          <h3 className="font-semibold text-ink">Clés API</h3>
          <p className="text-xs text-muted mt-0.5 mb-4">
            Stockées chiffrées. Prises en compte immédiatement, sans redémarrer.
          </p>
          <div className="divide-y divide-border/50">
            {(keys ?? []).map((k) => {
              const s = SERVICES[k.service];
              return (
                <div key={k.service} className="py-3 flex flex-col sm:flex-row sm:items-center gap-2">
                  <div className="sm:w-56 shrink-0">
                    <div className="flex items-center gap-2 text-sm font-medium text-ink">
                      <span className={`w-1.5 h-1.5 rounded-full ${k.configured ? "bg-risk-low" : "bg-border"}`} />
                      {s?.label ?? k.service}
                      {s && (
                        <a href={s.url} target="_blank" rel="noreferrer" className="text-muted hover:text-accent" title="Obtenir une clé">
                          <Icon name="external" size={13} />
                        </a>
                      )}
                    </div>
                    <div className="text-[11px] text-muted mt-0.5 pl-3.5">{s?.unlocks}</div>
                  </div>
                  <div className="flex gap-2 flex-1">
                    <input
                      type="password"
                      className="input flex-1"
                      placeholder={k.configured ? `configurée (${k.source === "env" ? ".env" : "ici"})` : "non configurée"}
                      value={draft[k.service] ?? ""}
                      onChange={(e) => setDraft((d) => ({ ...d, [k.service]: e.target.value }))}
                      onKeyDown={(e) => e.key === "Enter" && save(k.service)}
                    />
                    <button
                      className="btn btn-ghost"
                      disabled={!draft[k.service] || saving === k.service}
                      onClick={() => save(k.service)}
                    >
                      {saving === k.service ? "…" : "Enregistrer"}
                    </button>
                    {k.configured && k.source === "database" && (
                      <button
                        className="btn btn-ghost !px-3 text-risk-critical"
                        title="Supprimer la clé"
                        onClick={async () => {
                          await api.deleteApiKey(k.service);
                          await refresh();
                        }}
                      >
                        <Icon name="trash" size={15} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="card">
          <h3 className="font-semibold text-ink">Modules disponibles</h3>
          <p className="text-xs text-muted mt-0.5 mb-3">
            {ready} sur {(modules ?? []).length} prêts à l'emploi.
          </p>
          <div className="grid sm:grid-cols-2 gap-1.5">
            {(modules ?? []).map((m) => (
              <div key={m.name} className="flex items-center justify-between gap-2 text-[13px] py-1.5 px-2.5 rounded-xl bg-panel2/70">
                <span className="text-ink/85 truncate">{moduleLabel(m.name)}</span>
                <span className={`text-xs shrink-0 inline-flex items-center gap-1 ${m.available ? "text-[#1f7a35]" : "text-muted"}`}>
                  <Icon name={m.available ? "check" : "key"} size={12} />
                  {m.available ? "prêt" : "clé requise"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
