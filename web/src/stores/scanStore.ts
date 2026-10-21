import { create } from "zustand";
import type { WsEvent } from "../lib/types";

export interface ModuleProgress {
  name: string;
  status: "pending" | "running" | "ok" | "error" | "skipped";
  data?: any;
  error?: string;
}

interface ScanState {
  activeScanId: string | null;
  progress: number;
  modules: Record<string, ModuleProgress>;
  events: WsEvent[];
  finished: boolean;
  threatScore: number | null;
  start: (scanId: string) => void;
  applyEvent: (e: WsEvent) => void;
  reset: () => void;
  compareA: string | null;
  compareB: string | null;
  setCompare: (a: string | null, b: string | null) => void;
}

export const useScanStore = create<ScanState>((set) => ({
  activeScanId: null,
  progress: 0,
  modules: {},
  events: [],
  finished: false,
  threatScore: null,
  compareA: null,
  compareB: null,
  start: (scanId) =>
    set({ activeScanId: scanId, progress: 0, modules: {}, events: [], finished: false, threatScore: null }),
  applyEvent: (e) =>
    set((s) => {
      const modules = { ...s.modules };
      if (e.event === "scan_start" && e.modules) {
        for (const m of e.modules) modules[m] = { name: m, status: "pending" };
      } else if (e.event === "module_start" && e.module) {
        modules[e.module] = { name: e.module, status: "running" };
      } else if ((e.event === "module_complete" || e.event === "module_error") && e.module) {
        modules[e.module] = {
          name: e.module,
          status: (e.status as any) ?? "ok",
          data: e.data,
          error: e.data?.error,
        };
      }
      return {
        modules,
        events: [...s.events, e],
        progress: e.progress ?? s.progress,
        finished: e.event === "scan_complete" ? true : s.finished,
        threatScore: e.event === "scan_complete" ? e.threat_score ?? null : s.threatScore,
      };
    }),
  reset: () => set({ activeScanId: null, progress: 0, modules: {}, events: [], finished: false }),
  setCompare: (a, b) => set({ compareA: a, compareB: b }),
}));
