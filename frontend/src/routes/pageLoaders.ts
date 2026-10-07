// One source of truth for the lazily loaded pages. App.tsx renders them through
// React.lazy using these loaders, and prefetchPages() calls the very same dynamic
// imports early, so the browser already has the code when the route is opened.
export const pageLoaders = {
  // The sidebar frame around every signed-in page (not a page itself).
  appLayout: () => import("../layouts/AppLayout"),
  login: () => import("../pages/auth/Login"),
  register: () => import("../pages/auth/Register"),
  profile: () => import("../pages/profile/Profile"),
};

export type PageName = keyof typeof pageLoaders;

const PAGE_FOR_PATH: Record<string, PageName> = {
  "/login": "login",
  "/register": "register",
  "/profile": "profile",
};

// Pages shown inside AppLayout: prefetching one also fetches the layout, or
// opening it would still wait for the sidebar's code.
const SIGNED_IN_PAGES: ReadonlySet<PageName> = new Set(["profile"]);

export function prefetchPages(...names: PageName[]) {
  if (names.some((name) => SIGNED_IN_PAGES.has(name))) names = [...names, "appLayout"];
  for (const name of names) {
    // Best-effort: if the download fails, opening the route simply retries it.
    pageLoaders[name]().catch(() => undefined);
  }
}

export function prefetchPageForPath(path: string) {
  const name = PAGE_FOR_PATH[path];
  if (name) prefetchPages(name);
}
