import { UserRound, type LucideIcon } from "lucide-react";

export interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
  // Shown only to admins (the pages are also guarded by AdminRoute).
  adminOnly?: boolean;
}

// Every link in the sidebar. Add a link here only once its page exists, so
// nobody can click into a "Page not found". Planned, in order:
//   General: Projects (Phase 1), Hardware + My Loans (Phase 2), Events (Phase 4)
//   Admin:   Overview, Users, Loan requests, Hardware, Projects (Phase 3)
export const navGroups: NavGroup[] = [
  {
    label: "General",
    items: [{ label: "Profile", to: "/profile", icon: UserRound }],
  },
];
