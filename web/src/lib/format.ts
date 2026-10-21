import type { RiskLevel } from "./types";

export function riskColor(level: RiskLevel | string): string {
  switch (level) {
    case "critical":
      return "#b2453a"; // brick
    case "high":
      return "#c56b3c"; // burnt orange
    case "medium":
      return "#cf9a46"; // ochre
    default:
      return "#7fa07a"; // sage
  }
}

export function riskFromScore(score: number): RiskLevel {
  if (score >= 70) return "critical";
  if (score >= 40) return "high";
  if (score >= 20) return "medium";
  return "low";
}

export function detectType(value: string): string {
  const v = value.trim();
  if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v)) return "email";
  if (/^(\d{1,3}\.){3}\d{1,3}$/.test(v) || v.includes(":")) return "ip";
  if (/^(?!-)([a-z0-9-]{1,63}\.)+[a-z]{2,}$/i.test(v)) return "domain";
  if (/^[a-z0-9][a-z0-9._-]{1,38}$/i.test(v)) return "username";
  return "unknown";
}

export function timeAgo(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso).getTime();
  const s = Math.floor((Date.now() - d) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}
