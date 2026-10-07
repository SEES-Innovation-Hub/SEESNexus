import { ArrowLeftRight, Cpu, FolderKanban, UserRound, type LucideIcon } from "lucide-react";

export interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  // Hidden from visitors who aren't signed in.
  requiresAuth?: boolean;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
  // Shown only to admins (the pages are also guarded by AdminRoute).
  adminOnly?: boolean;
}

// Every link in the sidebar. Add a link here only once its page exists, so
// nobody can click into a "Page not found". Planned, in order:
//   General: Events (Phase 4)
//   Admin:   Overview, Users, Loan requests, Hardware, Projects (Phase 3)
export const navGroups: NavGroup[] = [
  {
    label: "General",
    items: [
      { label: "Projects", to: "/projects", icon: FolderKanban },
      { label: "Hardware", to: "/hardware", icon: Cpu },
      { label: "My Loans", to: "/loans", icon: ArrowLeftRight, requiresAuth: true },
      { label: "Profile", to: "/profile", icon: UserRound, requiresAuth: true },
    ],
  },
];
