export type TargetType = "domain" | "ip" | "email" | "username" | "unknown";
export type ScanStatus = "pending" | "running" | "completed" | "failed" | "cancelled";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface ModuleInfo {
  name: string;
  description: string;
  category: string;
  supported_types: TargetType[];
  requires_api_key: boolean;
  api_service: string | null;
  available: boolean;
}

export interface ResultItem {
  id: string;
  scan_id: string;
  module_name: string;
  status: "ok" | "error" | "skipped";
  data: Record<string, any>;
  confidence: number;
  tags: string[];
  error: string | null;
  created_at: string | null;
}

export interface ThreatFactor {
  points: number;
  reason: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  severity: RiskLevel | "safe" | "attention";
  [k: string]: any;
}
export interface GraphEdge {
  source: string;
  target: string;
  label: string;
}
export interface RelationGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ScanSummary {
  target: string;
  threat_score: number;
  threat_factors: ThreatFactor[];
  risk_level: RiskLevel;
  modules_ok: string[];
  modules_error: { module: string; error: string }[];
  modules_skipped: { module: string; reason: string }[];
  highlights: Record<string, any>;
  graph?: RelationGraph;
}

export interface Scan {
  id: string;
  target: string;
  target_type: TargetType;
  status: ScanStatus;
  threat_score: number;
  config: Record<string, any>;
  summary: ScanSummary;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
  tags: string[];
  notes: { id: string; content: string; created_at: string }[];
  results?: ResultItem[];
}

export interface DashboardStats {
  total_scans: number;
  unique_targets: number;
  threats_detected: number;
  avg_threat_score: number;
  activity: { date: string; count: number }[];
  recent: Scan[];
}

export interface WsEvent {
  event: string;
  scan_id?: string;
  module?: string;
  status?: string;
  progress?: number;
  data?: any;
  summary?: ScanSummary;
  threat_score?: number;
  target?: string;
  target_type?: string;
  modules?: string[];
  error?: string;
}
