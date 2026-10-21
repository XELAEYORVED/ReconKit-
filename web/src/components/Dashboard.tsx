import { Link } from "react-router-dom";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useStats } from "../lib/api";
import { riskColor, riskFromScore, timeAgo } from "../lib/format";

function Stat({ label, value, accent }: { label: string; value: any; accent?: string }) {
  return (
    <div className="card">
      <div className="text-xs text-muted uppercase tracking-widest">{label}</div>
      <div className="text-3xl font-bold font-mono mt-1" style={{ color: accent ?? "#d6f5e3" }}>
        {value}
      </div>
    </div>
  );
}

export function Dashboard() {
  const { data, isLoading } = useStats();
  if (isLoading || !data) return <div className="text-muted">Loading dashboard…</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Scans run" value={data.total_scans} accent="#0071e3" />
        <Stat label="Unique targets" value={data.unique_targets} accent="#0066cc" />
        <Stat label="Threats detected" value={data.threats_detected} accent="#ff9500" />
        <Stat label="Avg threat score" value={data.avg_threat_score} />
      </div>

      <div className="card">
        <div className="text-sm text-ink/80 mb-3">Scan activity</div>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data.activity}>
            <defs>
              <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0071e3" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#0071e3" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="date" stroke="#6b7280" fontSize={11} />
            <YAxis stroke="#6b7280" fontSize={11} allowDecimals={false} />
            <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #d2d2d7", color: "#1d1d1f", borderRadius: 8 }} />
            <Area type="monotone" dataKey="count" stroke="#0071e3" fill="url(#g)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <div className="text-sm text-ink/80 mb-3">Recent scans</div>
        <div className="space-y-1">
          {data.recent.map((s) => {
            const level = riskFromScore(s.threat_score);
            return (
              <Link
                key={s.id}
                to={`/results/${s.id}`}
                className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-panel2 text-sm"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ background: riskColor(level) }}
                  />
                  <span className="font-mono text-ink truncate">{s.target}</span>
                  <span className="text-[10px] text-muted">{s.target_type}</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted">
                  <span style={{ color: riskColor(level) }}>{s.threat_score}</span>
                  <span>{s.status}</span>
                  <span>{timeAgo(s.started_at)}</span>
                </div>
              </Link>
            );
          })}
          {data.recent.length === 0 && (
            <div className="text-muted text-sm py-6 text-center">
              No scans yet. <Link to="/scan" className="text-accent">Run your first scan →</Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
