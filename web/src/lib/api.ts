import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { DashboardStats, ModuleInfo, Scan } from "./types";

const TOKEN_KEY = "reconkit_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t: string | null) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

async function req<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  health: () => req<{ status: string; version: string; banner: string }>("/api/health"),
  authConfig: () => req<{ require_auth: boolean }>("/api/auth/config"),
  stats: () => req<DashboardStats>("/api/scans/stats"),
  modules: () => req<ModuleInfo[]>("/api/scans/modules"),
  listScans: (params = "") => req<Scan[]>(`/api/scans${params}`),
  getScan: (id: string) => req<Scan>(`/api/scans/${id}`),
  createScan: (body: { target: string; modules?: string[]; target_type?: string }) =>
    req<{ scan_id: string; status: string; ws: string }>("/api/scans", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteScan: (id: string) => req<void>(`/api/scans/${id}`, { method: "DELETE" }),
  compare: (a: string, b: string) => req<any>(`/api/compare/${a}/${b}`),
  apiKeys: () =>
    req<{ service: string; configured: boolean; source: string | null }[]>(
      "/api/settings/api-keys",
    ),
  setApiKey: (service: string, key: string) =>
    req("/api/settings/api-keys", { method: "PUT", body: JSON.stringify({ service, key }) }),
  deleteApiKey: (service: string) =>
    req<void>(`/api/settings/api-keys/${service}`, { method: "DELETE" }),
  reportUrl: (id: string, format: string) => `/api/reports/${id}?format=${format}`,
};

// --- React Query hooks ---
export const useStats = () =>
  useQuery({ queryKey: ["stats"], queryFn: api.stats, refetchInterval: 15000 });

export const useModules = () =>
  useQuery({ queryKey: ["modules"], queryFn: api.modules });

export const useScans = (params = "") =>
  useQuery({ queryKey: ["scans", params], queryFn: () => api.listScans(params) });

export const useScan = (id: string | undefined, poll = false) =>
  useQuery({
    queryKey: ["scan", id],
    queryFn: () => api.getScan(id!),
    enabled: !!id,
    refetchInterval: poll ? 2500 : false,
  });

export function useCreateScan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.createScan,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scans"] }),
  });
}

export function useDeleteScan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.deleteScan,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["scans"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}
