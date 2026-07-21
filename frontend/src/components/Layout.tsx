import { NavLink, Outlet } from "react-router-dom";
import { HealthBadge } from "./HealthBadge";

const NAV = [
  { to: "/", label: "Fleet Overview", end: true },
  { to: "/drives", label: "Drive Details" },
  { to: "/predictions", label: "Prediction Explorer" },
  { to: "/chat", label: "AI Chat" },
  { to: "/metrics", label: "System Metrics" },
];

export function Layout() {
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight">
            Nexus<span className="text-nexus-accent">SSD</span>
          </span>
          <span className="text-xs text-slate-500">Fleet Health Copilot</span>
        </div>
        <HealthBadge />
      </header>

      <div className="flex">
        <nav className="w-52 shrink-0 border-r border-white/10 p-4">
          <ul className="space-y-1">
            {NAV.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    `block rounded-md px-3 py-2 text-sm ${
                      isActive
                        ? "bg-nexus-accent/20 text-white"
                        : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
