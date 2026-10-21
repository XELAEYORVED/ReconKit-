import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Sidebar } from "./Sidebar";

export function Layout({ children }: { children: ReactNode }) {
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: api.health });

  return (
    <div className="flex min-h-screen bg-base text-gray-200">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="border-b border-border bg-panel/80 backdrop-blur px-6 py-2 flex items-center justify-between sticky top-0 z-20">
          <div className="text-xs text-gray-400 font-mono">
            <span className="text-neon">ReconKit</span> — Passive OSINT Only · Usage responsable
            et légal uniquement
          </div>
          <div className="flex items-center gap-2 text-[11px] text-gray-500">
            <span className="w-2 h-2 rounded-full bg-neon animate-pulse" />
            {health ? `API v${health.version}` : "connecting…"}
          </div>
        </header>
        <main className="flex-1 p-6 overflow-x-hidden">{children}</main>
      </div>
    </div>
  );
}
