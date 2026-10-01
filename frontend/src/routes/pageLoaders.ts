// One source of truth for the lazily loaded pages. App.tsx renders them through
// React.lazy using these loaders, and prefetchPages() calls the very same dynamic
// imports early, so the browser already has the code when the route is opened.
export const pageLoaders = {
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

export function prefetchPages(...names: PageName[]) {
  for (const name of names) {
    // Best-effort: if the download fails, opening the route simply retries it.
    pageLoaders[name]().catch(() => undefined);
  }
}

export function prefetchPageForPath(path: string) {
  const name = PAGE_FOR_PATH[path];
  if (name) prefetchPages(name);
}
