import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Logo, MobileNav, Sidebar } from "./Sidebar";

export function Layout({ children }: { children: ReactNode }) {
  const { data: health, isError } = useQuery({ queryKey: ["health"], queryFn: api.health, retry: 1 });

  return (
    <div className="flex min-h-screen bg-base text-ink">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="glass border-b border-border/70 px-4 md:px-8 h-14 flex items-center justify-between sticky top-0 z-20">
          <div className="md:hidden">
            <Logo />
          </div>
          <div className="hidden md:block text-[13px] text-muted">
            Usage responsable et légal uniquement
          </div>
          <div className="flex items-center gap-2 text-[11px] text-muted">
            <span className={`w-1.5 h-1.5 rounded-full ${isError ? "bg-risk-critical" : health ? "bg-risk-low" : "bg-border"}`} />
            {isError ? "API hors ligne" : health ? `API v${health.version}` : "connexion…"}
          </div>
        </header>
        <main className="flex-1 px-4 pt-6 pb-24 md:px-10 md:pt-10 md:pb-12 overflow-x-hidden max-w-[1200px] w-full mx-auto">
          {children}
        </main>
      </div>
      <MobileNav />
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: ReactNode; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="flex items-end justify-between gap-4 flex-wrap mb-6">
      <div className="min-w-0">
        <h1 className="text-[28px] md:text-[34px] leading-tight">{title}</h1>
        {subtitle && <p className="text-muted text-[15px] mt-1">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
