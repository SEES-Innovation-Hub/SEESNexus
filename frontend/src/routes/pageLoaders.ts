// One source of truth for the lazily loaded pages. App.tsx renders them through
// React.lazy using these loaders, and prefetchPages() calls the very same dynamic
// imports early, so the browser already has the code when the route is opened.
export const pageLoaders = {
  // The sidebar frame around the app's inner pages (not a page itself).
  appLayout: () => import("../layouts/AppLayout"),
  login: () => import("../pages/auth/Login"),
  register: () => import("../pages/auth/Register"),
  profile: () => import("../pages/profile/Profile"),
  projectsList: () => import("../pages/projects/ProjectsList"),
  projectDetail: () => import("../pages/projects/ProjectDetail"),
  newProject: () => import("../pages/projects/NewProject"),
  editProject: () => import("../pages/projects/EditProject"),
  hardwareList: () => import("../pages/hardware/HardwareList"),
  myLoans: () => import("../pages/loans/MyLoans"),
  dashboard: () => import("../pages/dashboard/Dashboard"),
  adminOverview: () => import("../pages/admin/AdminOverview"),
  adminLoans: () => import("../pages/admin/AdminLoans"),
  adminUsers: () => import("../pages/admin/AdminUsers"),
  adminHardware: () => import("../pages/admin/AdminHardware"),
};

export type PageName = keyof typeof pageLoaders;

const PAGE_FOR_PATH: Record<string, PageName> = {
  "/login": "login",
  "/register": "register",
  "/profile": "profile",
  "/projects": "projectsList",
  "/projects/new": "newProject",
  "/hardware": "hardwareList",
  "/loans": "myLoans",
  "/dashboard": "dashboard",
  "/admin": "adminOverview",
  "/admin/loans": "adminLoans",
  "/admin/users": "adminUsers",
  "/admin/hardware": "adminHardware",
};

// Paths with an id in them, checked when there is no exact match above.
const PAGE_FOR_PATTERN: [RegExp, PageName][] = [
  [/^\/projects\/[^/]+\/edit$/, "editProject"],
  [/^\/projects\/[^/]+$/, "projectDetail"],
];

// Pages shown inside AppLayout: prefetching one also fetches the layout, or
// opening it would still wait for the sidebar's code.
const LAYOUT_PAGES: ReadonlySet<PageName> = new Set([
  "profile",
  "projectsList",
  "projectDetail",
  "newProject",
  "editProject",
  "hardwareList",
  "myLoans",
  "dashboard",
  "adminOverview",
  "adminLoans",
  "adminUsers",
  "adminHardware",
]);

export function prefetchPages(...names: PageName[]) {
  if (names.some((name) => LAYOUT_PAGES.has(name))) names = [...names, "appLayout"];
  for (const name of names) {
    // Best-effort: if the download fails, opening the route simply retries it.
    pageLoaders[name]().catch(() => undefined);
  }
}

export function prefetchPageForPath(path: string) {
  const name = PAGE_FOR_PATH[path] ?? PAGE_FOR_PATTERN.find(([pattern]) => pattern.test(path))?.[1];
  if (name) prefetchPages(name);
}
