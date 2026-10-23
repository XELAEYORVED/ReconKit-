import { riskColor, riskFromScore } from "../lib/format";
import { RISK_LABEL } from "../lib/modules";

export function ThreatScore({ score, size = 160 }: { score: number; size?: number }) {
  const level = riskFromScore(score);
  const color = riskColor(level);
  const stroke = Math.max(8, size / 14);
  const r = size / 2 - stroke;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - Math.min(100, score) / 100);

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e8e8ed" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease, stroke 0.4s" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display font-semibold tabular-nums leading-none" style={{ color, fontSize: size * 0.27 }}>
          {score}
        </span>
        <span className="text-muted mt-1" style={{ fontSize: Math.max(10, size * 0.08) }}>
          risque {RISK_LABEL[level].toLowerCase()}
        </span>
      </div>
    </div>
  );
}
