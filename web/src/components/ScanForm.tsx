import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateScan, useModules } from "../lib/api";
import { detectType } from "../lib/format";
import { moduleLabel, MODULES, TYPE_LABEL } from "../lib/modules";
import { useScanStore } from "../stores/scanStore";
import { Icon, type IconName } from "./Icon";

const EXAMPLES: { value: string; kind: string; icon: IconName; hint: string }[] = [
  { value: "example.com", kind: "domain", icon: "globe", hint: "Un site web" },
  { value: "8.8.8.8", kind: "ip", icon: "server", hint: "Une adresse IP" },
  { value: "prenom@entreprise.com", kind: "email", icon: "mail", hint: "Un email" },
  { value: "johndoe", kind: "username", icon: "user", hint: "Un pseudo" },
];

const TIPS: Record<string, string> = {
  domain: "Le scan le plus complet : propriétaire, DNS, sous-domaines, sécurité du site, technologies…",
  ip: "Localisation, hébergeur, réseau et ports exposés du serveur.",
  email: "Type de fournisseur, sécurité du domaine, profil Gravatar. Les fuites de données demandent une clé HIBP.",
  username: "Recherche ce pseudo sur les principaux réseaux sociaux.",
};

export function ScanForm() {
  const [target, setTarget] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [advanced, setAdvanced] = useState(false);
  const { data: modules } = useModules();
  const createScan = useCreateScan();
  const start = useScanStore((s) => s.start);
  const navigate = useNavigate();

  const value = target.trim();
  const detected = useMemo(() => detectType(value), [value]);
  const valid = value !== "" && detected !== "unknown";

  const applicable = useMemo(
    () => (modules ?? []).filter((m) => valid && m.supported_types.includes(detected as any)),
    [modules, detected, valid],
  );
  const ready = applicable.filter((m) => m.available);

  const toggle = (name: string) =>
    setSelected((s) => (s.includes(name) ? s.filter((x) => x !== name) : [...s, name]));

  const submit = async () => {
    if (!valid) return;
    const res = await createScan.mutateAsync({
      target: value,
      modules: advanced && selected.length > 0 ? selected : undefined,
    });
    start(res.scan_id);
    navigate(`/scan/${res.scan_id}`);
  };

  const error = createScan.isError ? (createScan.error as Error).message.replace(/^\d+:\s*/, "") : null;

  return (
    <div className="card !p-5 md:!p-7 space-y-5">
      <div>
        <label htmlFor="target" className="text-sm font-medium text-ink">Que veux-tu analyser ?</label>
        <div className="flex flex-col sm:flex-row gap-2 mt-2">
          <div className="relative flex-1">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted">
              <Icon name="scan" size={18} />
            </span>
            <input
              id="target"
              autoFocus
              className="input !pl-10 !py-3 !text-[16px]"
              placeholder="example.com, 8.8.8.8, email ou pseudo"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              autoComplete="off"
              spellCheck={false}
            />
          </div>
          <button
            className="btn btn-primary !py-3 !px-6 whitespace-nowrap disabled:opacity-40 disabled:shadow-none"
            disabled={!valid || createScan.isPending}
            onClick={submit}
          >
            {createScan.isPending ? "Lancement…" : "Lancer le scan"}
          </button>
        </div>

        <div className="mt-2.5 min-h-[20px] text-[13px]">
          {value === "" && <span className="text-muted">Une seule valeur, sans espaces et sans http://</span>}
          {value !== "" && valid && (
            <span className="text-ink/80">
              <span className="inline-flex items-center gap-1 bg-accent/10 text-accent rounded-full px-2 py-0.5 text-xs font-medium mr-2">
                <Icon name="check" size={12} /> {TYPE_LABEL[detected]}
              </span>
              {TIPS[detected]}
            </span>
          )}
          {value !== "" && !valid && (
            <span className="text-[#c4271d] inline-flex items-center gap-1.5">
              <Icon name="alert" size={14} />
              Format non reconnu. Exemples valides : example.com · 8.8.8.8 · nom@site.com · johndoe
              {value.includes(" ") && " (pas d'espaces : ReconKit ne cherche pas une personne par son nom)"}
            </span>
          )}
        </div>
        {error && (
          <div className="mt-2 text-[13px] rounded-xl px-3 py-2 bg-risk-critical/10 text-[#c4271d]">{error}</div>
        )}
      </div>

      {value === "" && (
        <div>
          <div className="text-xs text-muted mb-2">Ou essaie un exemple :</div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.value}
                type="button"
                onClick={() => setTarget(ex.value)}
                className="text-left rounded-2xl border border-border/70 bg-panel2/50 hover:border-accent hover:bg-accent/5 px-3.5 py-3 transition-colors"
              >
                <div className="flex items-center gap-2 text-xs text-muted">
                  <Icon name={ex.icon} size={14} /> {ex.hint}
                </div>
                <div className="font-mono text-[13px] text-ink mt-1 truncate">{ex.value}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {valid && applicable.length > 0 && (
        <div className="border-t border-border/60 pt-4">
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="text-sm text-ink">
              Ce qui sera vérifié{" "}
              <span className="text-muted">
                ({ready.length} prêt{ready.length > 1 ? "s" : ""} sur {applicable.length})
              </span>
            </div>
            <button className="text-xs text-accent hover:underline" onClick={() => setAdvanced((a) => !a)}>
              {advanced ? "Tout vérifier" : "Choisir les modules"}
            </button>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-1.5">
            {applicable.map((m) => {
              const on = !advanced || selected.includes(m.name);
              return (
                <button
                  key={m.name}
                  type="button"
                  disabled={!advanced}
                  onClick={() => toggle(m.name)}
                  title={MODULES[m.name]?.plain ?? m.description}
                  className={`flex items-center gap-2 text-left text-[13px] px-2.5 py-1.5 rounded-xl border transition-colors ${
                    advanced ? (on ? "border-accent bg-accent/5" : "border-border/60 hover:border-accent/50") : "border-transparent"
                  } ${!m.available ? "opacity-55" : ""}`}
                >
                  <span className={m.available ? (on ? "text-risk-low" : "text-border") : "text-muted"}>
                    <Icon name={m.available ? "check" : "key"} size={14} />
                  </span>
                  <span className="truncate text-ink/85">{moduleLabel(m.name)}</span>
                  {!m.available && <span className="ml-auto text-[10px] text-muted shrink-0">clé API</span>}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
