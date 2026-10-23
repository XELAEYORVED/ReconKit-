import { NavLink } from "react-router-dom";
import { Icon, type IconName } from "./Icon";

export const NAV_LINKS: { to: string; label: string; icon: IconName }[] = [
  { to: "/", label: "Tableau de bord", icon: "dashboard" },
  { to: "/scan", label: "Nouveau scan", icon: "scan" },
  { to: "/history", label: "Historique", icon: "history" },
  { to: "/compare", label: "Comparer", icon: "compare" },
  { to: "/settings", label: "Réglages", icon: "settings" },
];

export function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <span className="inline-flex items-center justify-center w-8 h-8 rounded-[10px] bg-gradient-to-br from-[#2a8cff] to-accent text-white shadow-accent">
        <Icon name="scan" size={16} />
      </span>
      <span className="font-display text-[18px] font-semibold tracking-tight text-ink">ReconKit</span>
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r border-border/70 glass h-screen sticky top-0 p-4 hidden md:flex md:flex-col">
      <div className="px-2 pt-2 pb-5">
        <Logo />
        <div className="mt-1.5 ml-[42px] text-[10px] text-muted uppercase tracking-[0.2em]">OSINT passif</div>
      </div>

      <nav className="space-y-0.5">
        {NAV_LINKS.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-xl text-[14px] font-medium transition-colors ${
                isActive ? "bg-accent/10 text-accent" : "text-ink/75 hover:bg-black/[0.04] hover:text-ink"
              }`
            }
          >
            <Icon name={l.icon} size={17} />
            {l.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto rounded-2xl bg-panel2 border border-border/60 p-3 text-[11px] text-muted leading-relaxed">
        <div className="flex items-center gap-1.5 text-ink/80 font-medium mb-1">
          <Icon name="shield" size={13} /> 100 % passif
        </div>
        Uniquement des sources publiques. Aucun contact direct avec la cible.
      </div>
    </aside>
  );
}

/** Bottom tab bar on small screens (the sidebar is hidden there). */
export function MobileNav() {
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-30 glass border-t border-border/70 flex justify-around px-2 pb-[env(safe-area-inset-bottom)]">
      {NAV_LINKS.map((l) => (
        <NavLink
          key={l.to}
          to={l.to}
          end={l.to === "/"}
          className={({ isActive }) =>
            `flex flex-col items-center gap-0.5 py-2 px-2 text-[10px] font-medium ${isActive ? "text-accent" : "text-muted"}`
          }
        >
          <Icon name={l.icon} size={20} />
          {l.label.split(" ")[0]}
        </NavLink>
      ))}
    </nav>
  );
}
