import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard", icon: "◉" },
  { to: "/scan", label: "New Scan", icon: "✛" },
  { to: "/history", label: "History", icon: "≣" },
  { to: "/compare", label: "Compare", icon: "⇄" },
  { to: "/settings", label: "Settings", icon: "⚙" },
];

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r border-border/70 glass min-h-screen p-4 hidden md:flex md:flex-col">
      <div className="px-2 py-3 mb-2">
        <div className="flex items-center gap-2.5">
          <span className="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-accent text-white text-[13px] font-semibold shadow-accent">
            R
          </span>
          <span className="font-display text-[19px] font-semibold tracking-tight text-ink">
            ReconKit
          </span>
        </div>
        <div className="mt-1.5 ml-[38px] text-[10px] text-muted uppercase tracking-[0.2em]">
          passive osint
        </div>
      </div>

      <nav className="space-y-0.5">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-xl text-[14px] font-medium transition-colors ${
                isActive
                  ? "bg-black/[0.06] text-accent"
                  : "text-ink/80 hover:bg-black/[0.04] hover:text-ink"
              }`
            }
          >
            <span className="w-4 text-center text-[15px] leading-none">{l.icon}</span>
            {l.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto pt-6 text-[11px] text-muted leading-relaxed">
        100% passive reconnaissance.
        <br />
        No active scanning, no intrusion.
      </div>
    </aside>
  );
}
