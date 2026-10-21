import { riskColor, riskFromScore } from "../lib/format";

export function ThreatScore({ score, size = 160 }: { score: number; size?: number }) {
  const level = riskFromScore(score);
  const color = riskColor(level);
  const r = size / 2 - 12;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - score / 100);

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#d2d2d7" strokeWidth={10} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease, stroke 0.4s" }}
        />
      </svg>
      <div className="-mt-[calc(50%+8px)] flex flex-col items-center pointer-events-none" style={{ marginTop: -(size / 2) - 20 }}>
        <span className="text-4xl font-bold font-mono" style={{ color }}>
          {score}
        </span>
        <span className="text-xs uppercase tracking-widest" style={{ color }}>
          {level}
        </span>
      </div>
    </div>
  );
}
