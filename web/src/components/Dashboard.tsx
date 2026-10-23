import { Link } from "react-router-dom";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useStats } from "../lib/api";
import { riskColor, riskFromScore, timeAgo } from "../lib/format";
import { RISK_LABEL, TYPE_LABEL } from "../lib/modules";
import { Icon, type IconName } from "./Icon";

function Stat({ label, value, icon, color }: { label: string; value: any; icon: IconName; color: string }) {
  return (
    <div className="card flex items-center gap-4">
      <span className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${color}1a`, color }}>
        <Icon name={icon} size={20} />
      </span>
      <div>
        <div className="text-[26px] font-display font-semibold leading-none tabular-nums text-ink">{value}</div>
        <div className="text-xs text-muted mt-1">{label}</div>
      </div>
    </div>
  );
}

const STEPS: { icon: IconName; title: string; text: string }[] = [
  { icon: "scan", title: "1. Entre une cible", text: "Un site (example.com), une IP, un email ou un pseudo." },
  { icon: "clock", title: "2. Laisse tourner", text: "ReconKit interroge des sources publiques, en direct." },
  { icon: "shield", title: "3. Lis le bilan", text: "Un score de risque expliqué et des fiches claires." },
];

export function Dashboard() {
  const { data, isLoading } = useStats();
  if (isLoading || !data) return <div className="text-muted">Chargement…</div>;

  return (
    <div className="space-y-6">
      <div className="card !p-6 md:!p-8 bg-gradient-to-br from-white to-[#eef5ff] relative overflow-hidden">
        <div className="max-w-xl">
          <h2 className="text-[22px] md:text-[26px] font-semibold text-ink">Que sait Internet sur une cible ?</h2>
          <p className="text-muted mt-2 text-[15px]">
            ReconKit rassemble les informations publiques sur un site, une adresse IP, un email ou un pseudo, puis te
            dit ce qui pose problème.
          </p>
          <Link to="/scan" className="btn btn-primary inline-flex items-center gap-2 mt-5">
            Lancer un scan <Icon name="arrow" size={16} />
          </Link>
        </div>
        <div className="grid sm:grid-cols-3 gap-3 mt-7">
          {STEPS.map((s) => (
            <div key={s.title} className="rounded-2xl bg-white/80 border border-border/60 p-3.5">
              <div className="flex items-center gap-2 text-ink font-medium text-sm">
                <span className="text-accent"><Icon name={s.icon} size={16} /></span>
                {s.title}
              </div>
              <div className="text-xs text-muted mt-1">{s.text}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Scans lancés" value={data.total_scans} icon="scan" color="#0071e3" />
        <Stat label="Cibles différentes" value={data.unique_targets} icon="globe" color="#5856d6" />
        <Stat label="Cibles à risque" value={data.threats_detected} icon="alert" color="#ff9500" />
        <Stat label="Score moyen" value={data.avg_threat_score} icon="shield" color="#34c759" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="card lg:col-span-3">
          <div className="text-sm font-medium text-ink mb-3">Derniers scans</div>
          <div className="divide-y divide-border/50">
            {data.recent.map((s) => {
              const level = riskFromScore(s.threat_score);
              return (
                <Link
                  key={s.id}
                  to={s.status === "failed" ? `/scan/${s.id}` : `/results/${s.id}`}
                  className="flex items-center justify-between gap-3 py-2.5 px-1 hover:bg-panel2/60 rounded-lg text-sm"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: riskColor(level) }} />
                    <span className="font-medium text-ink truncate">{s.target}</span>
                    <span className="text-[11px] text-muted bg-panel2 rounded-full px-2 py-0.5 shrink-0">
                      {TYPE_LABEL[s.target_type] ?? s.target_type}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted shrink-0">
                    {s.status === "failed" ? (
                      <span className="text-risk-critical">échoué</span>
                    ) : (
                      <span className="font-medium tabular-nums" style={{ color: riskColor(level) }}>
                        {s.threat_score} · {RISK_LABEL[level]}
                      </span>
                    )}
                    <span className="hidden sm:inline">{timeAgo(s.started_at)}</span>
                  </div>
                </Link>
              );
            })}
            {data.recent.length === 0 && (
              <div className="text-muted text-sm py-8 text-center">
                Aucun scan pour l'instant.{" "}
                <Link to="/scan" className="text-accent">Lance le premier →</Link>
              </div>
            )}
          </div>
        </div>

        <div className="card lg:col-span-2">
          <div className="text-sm font-medium text-ink mb-3">Activité</div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data.activity}>
              <defs>
                <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#0071e3" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#0071e3" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" stroke="#6e6e73" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#6e6e73" fontSize={11} allowDecimals={false} tickLine={false} axisLine={false} width={24} />
              <Tooltip
                formatter={(v) => [v, "scans"]}
                contentStyle={{ background: "#fff", border: "1px solid #d2d2d7", borderRadius: 12, fontSize: 12 }}
              />
              <Area type="monotone" dataKey="count" stroke="#0071e3" fill="url(#g)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
