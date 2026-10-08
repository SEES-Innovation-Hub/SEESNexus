import { NavLink } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { navGroups } from "./navItems";

interface SidebarNavProps {
  // Icons only (the narrow desktop sidebar); labels stay for screen readers.
  collapsed: boolean;
  // Called after a link is clicked (the phone drawer closes itself).
  onNavigate?: () => void;
}

// 44px links for touch; 40px only on a laptop-width screen used with a mouse
// (pointer-fine), so nine links fit without scrolling. A tablet held sideways
// is laptop-width but touch, and keeps 44px.
const linkBase =
  "flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors lg:pointer-fine:min-h-10";

export function SidebarNav({ collapsed, onNavigate }: SidebarNavProps) {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  const groups = navGroups.filter((group) => !group.adminOnly || isAdmin);

  return (
    <nav aria-label="Main" className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
      {groups.map((group) => (
        <div key={group.label}>
          <p
            className={`mb-2 px-3 font-mono text-xs tracking-wide text-white/40 uppercase ${collapsed ? "sr-only" : ""}`}
          >
            {group.label}
          </p>
          <ul className="space-y-1">
            {group.items.map(({ label, to, icon: Icon, exact }) => (
              <li key={to}>
                {/* NavLink sets aria-current="page" on the link for the open page. */}
                <NavLink
                  to={to}
                  end={exact}
                  onClick={onNavigate}
                  title={collapsed ? label : undefined}
                  className={({ isActive }) =>
                    `${linkBase} ${collapsed ? "justify-center" : ""} ${
                      isActive
                        ? "bg-sees-mint/10 text-sees-mint"
                        : "text-white/70 hover:bg-sees-mint/5 hover:text-white"
                    }`
                  }
                >
                  <Icon aria-hidden="true" className="size-5 shrink-0" />
                  <span className={collapsed ? "sr-only" : "truncate"}>{label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}
