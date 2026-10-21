import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard", icon: "▣" },
  { to: "/scan", label: "New Scan", icon: "◎" },
  { to: "/history", label: "History", icon: "≣" },
  { to: "/compare", label: "Compare", icon: "⇄" },
  { to: "/settings", label: "Settings", icon: "⚙" },
];

export function Sidebar() {
  return (
    <aside className="w-56 shrink-0 border-r border-border bg-panel min-h-screen p-4 hidden md:block">
      <div className="mb-6">
        <div className="text-neon font-mono text-xl font-bold tracking-wider">ReconKit</div>
        <div className="text-[10px] text-gray-500 uppercase tracking-widest">passive osint</div>
      </div>
      <nav className="space-y-1">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-panel2 text-neon shadow-neon"
                  : "text-gray-400 hover:text-neon hover:bg-panel2"
              }`
            }
          >
            <span className="w-4 text-center">{l.icon}</span>
            {l.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-8 text-[10px] text-gray-600 leading-relaxed border-t border-border pt-4">
        100% passive reconnaissance. No active scanning, no intrusion.
      </div>
    </aside>
  );
}
