import { Menu, PanelLeftClose, PanelLeftOpen, X } from "lucide-react";
import { Suspense, useEffect, useState } from "react";
import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useModalDialog } from "../hooks/useModalDialog";
import { redirectPathForRole } from "../utils/redirectPathForRole";
import { SidebarNav } from "./sidebar/SidebarNav";
import { UserMenu } from "./sidebar/UserMenu";

// The frame around every signed-in page: a sidebar on laptops (lg, 1024px+) and,
// below that, a top bar whose ☰ button opens the same sidebar as a drawer.
// Landing, Login and Register don't use it.

const COLLAPSED_KEY = "sees.sidebar.collapsed";
const DESKTOP_QUERY = "(min-width: 1024px)";

// Remembering the collapsed sidebar is a per-browser convenience: blocked
// storage just means it starts expanded.
function readCollapsed() {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === "1";
  } catch {
    return false;
  }
}

function saveCollapsed(collapsed: boolean) {
  try {
    localStorage.setItem(COLLAPSED_KEY, collapsed ? "1" : "0");
  } catch {
    // Not saved; the sidebar still works.
  }
}

const iconButtonClassName =
  "inline-flex size-11 shrink-0 items-center justify-center rounded-lg text-white/60 hover:bg-sees-mint/5 hover:text-white";

// Goes to the member's home page; Landing is only for visitors.
function Logo({ collapsed = false }: { collapsed?: boolean }) {
  const { user } = useAuth();
  return (
    <Link
      to={user ? redirectPathForRole(user.role) : "/"}
      aria-label={collapsed ? "SEES Nexus home" : undefined}
      className="inline-flex min-h-11 min-w-0 items-center gap-2 font-semibold text-sees-mint"
    >
      <span
        aria-hidden="true"
        className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-sees-mint font-mono text-sm text-sees-forest"
      >
        S
      </span>
      {!collapsed && <span className="truncate">SEES Nexus</span>}
    </Link>
  );
}

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(readCollapsed);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const drawerRef = useModalDialog(drawerOpen);
  const closeDrawer = () => setDrawerOpen(false);

  function toggleCollapsed() {
    const next = !collapsed;
    setCollapsed(next);
    saveCollapsed(next);
  }

  // If the window is widened to laptop size while the drawer is open, close it:
  // the desktop sidebar takes over, and an open modal would keep the page inert.
  // Screen size is outside React, hence an effect.
  useEffect(() => {
    const desktop = window.matchMedia(DESKTOP_QUERY);
    const onChange = () => {
      if (desktop.matches) setDrawerOpen(false);
    };
    desktop.addEventListener("change", onChange);
    return () => desktop.removeEventListener("change", onChange);
  }, []);

  return (
    <div className="min-h-screen lg:flex">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded focus:bg-sees-mint focus:px-4 focus:py-2 focus:text-sees-forest"
      >
        Skip to content
      </a>

      {/* Laptop sidebar */}
      <aside
        className={`sticky top-0 hidden h-screen shrink-0 flex-col border-r border-sees-teal/40 bg-sees-void/70 transition-[width] duration-200 motion-reduce:transition-none lg:flex ${
          collapsed ? "w-[4.5rem]" : "w-64"
        }`}
      >
        <div className={`flex items-center gap-2 px-3 pt-4 ${collapsed ? "flex-col" : "justify-between"}`}>
          <Logo collapsed={collapsed} />
          <button
            type="button"
            onClick={toggleCollapsed}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
            className={iconButtonClassName}
          >
            {collapsed ? (
              <PanelLeftOpen aria-hidden="true" className="size-5" />
            ) : (
              <PanelLeftClose aria-hidden="true" className="size-5" />
            )}
          </button>
        </div>
        <SidebarNav collapsed={collapsed} />
        <UserMenu collapsed={collapsed} />
      </aside>

      <div className="min-w-0 flex-1">
        {/* Phone and tablet top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-2 border-b border-sees-teal/40 bg-sees-void/90 px-2 lg:hidden">
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open menu"
            aria-expanded={drawerOpen}
            className={iconButtonClassName}
          >
            <Menu aria-hidden="true" className="size-6" />
          </button>
          <Logo />
        </header>

        <main id="main" tabIndex={-1} className="px-4 py-8 outline-none sm:px-6 lg:px-10 lg:py-10">
          {/* Keeps the sidebar on screen while a page's code downloads. */}
          <Suspense fallback={null}>
            <Outlet />
          </Suspense>
        </main>
      </div>

      {/* Phone and tablet drawer: the same sidebar, sliding in from the left. */}
      <dialog
        ref={drawerRef}
        aria-label="Menu"
        onCancel={(event) => {
          event.preventDefault();
          closeDrawer();
        }}
        // The panel fills the dialog, so a click on the dialog itself is the backdrop.
        onClick={(event) => {
          if (event.target === event.currentTarget) closeDrawer();
        }}
        // Slides in AND out. A closing <dialog> is normally hidden in one frame;
        // transition-discrete (allow-discrete on display/overlay) keeps it on screen
        // until the slide-out ends. Browsers without it simply close instantly.
        // starting:open: is where the slide-in starts from.
        className="m-0 h-dvh max-h-none w-72 max-w-[85vw] -translate-x-full border-r border-sees-teal/60 bg-sees-void p-0 text-white transition-[translate,overlay,display] transition-discrete duration-200 ease-out backdrop:bg-black/60 backdrop:opacity-0 backdrop:transition-[opacity,overlay,display] backdrop:transition-discrete backdrop:duration-200 open:translate-x-0 open:backdrop:opacity-100 motion-reduce:transition-none motion-reduce:backdrop:transition-none starting:open:-translate-x-full starting:open:backdrop:opacity-0 lg:hidden"
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between gap-2 px-3 pt-4">
            <Logo />
            <button type="button" onClick={closeDrawer} aria-label="Close menu" className={iconButtonClassName}>
              <X aria-hidden="true" className="size-5" />
            </button>
          </div>
          <SidebarNav collapsed={false} onNavigate={closeDrawer} />
          <UserMenu collapsed={false} onNavigate={closeDrawer} />
        </div>
      </dialog>
    </div>
  );
}
