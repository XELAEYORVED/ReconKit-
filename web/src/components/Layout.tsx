import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Sidebar } from "./Sidebar";

export function Layout({ children }: { children: ReactNode }) {
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: api.health });

  return (
    <div className="flex min-h-screen bg-base text-ink">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="glass border-b border-border/70 px-6 py-3 flex items-center justify-between sticky top-0 z-20">
          <div className="text-[13px] text-muted">
            <span className="text-ink font-semibold">ReconKit</span>
            <span className="mx-2 text-border">·</span>
            Passive OSINT only — responsible &amp; lawful use
          </div>
          <div className="flex items-center gap-2 text-[11px] text-muted">
            <span className="w-1.5 h-1.5 rounded-full bg-risk-low" />
            {health ? `API v${health.version}` : "connecting…"}
          </div>
        </header>
        <main className="flex-1 px-6 py-8 md:px-10 overflow-x-hidden max-w-[1200px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
