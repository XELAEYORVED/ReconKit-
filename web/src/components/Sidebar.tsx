import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard", icon: "◧" },
  { to: "/scan", label: "New Scan", icon: "◉" },
  { to: "/history", label: "History", icon: "☰" },
  { to: "/compare", label: "Compare", icon: "⇆" },
  { to: "/settings", label: "Settings", icon: "⚙" },
];

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r border-border bg-panel min-h-screen p-5 hidden md:flex md:flex-col">
      <div className="mb-6">
        <div className="flex items-center gap-2.5">
          <span className="inline-block w-3.5 h-3.5 rotate-45 bg-accent shadow-accent" />
          <span className="font-display text-2xl font-semibold tracking-tight text-ink">
            ReconKit
          </span>
        </div>
        <div className="mt-1 ml-6 text-[10px] text-muted uppercase tracking-[0.25em]">
          passive osint
        </div>
      </div>

      <div className="rule-accent mb-5" />

      <nav className="space-y-1">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors border-l-2 ${
                isActive
                  ? "bg-panel2 text-accent border-accent"
                  : "text-muted hover:text-ink hover:bg-panel2/60 border-transparent"
              }`
            }
          >
            <span className="w-4 text-center text-base leading-none">{l.icon}</span>
            {l.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto pt-6 text-[10px] text-muted/70 leading-relaxed border-t border-border">
        100% passive reconnaissance.
        <br />
        No active scanning, no intrusion.
      </div>
    </aside>
  );
}
