import {
  ArrowLeftRight,
  Boxes,
  CalendarDays,
  CalendarCheck,
  ClipboardCheck,
  Cpu,
  FolderKanban,
  LayoutDashboard,
  Newspaper,
  ShieldCheck,
  UserRound,
  Users,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  // Highlight only on this exact address, not on pages below it (/admin must
  // not stay highlighted on /admin/loans).
  exact?: boolean;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
  // Shown only to admins (the pages are also guarded by AdminRoute).
  adminOnly?: boolean;
}

// Every link in the sidebar. Add a link here only once its page exists, so
// nobody can click into a "Page not found".
export const navGroups: NavGroup[] = [
  {
    label: "General",
    items: [
      { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
      { label: "Projects", to: "/projects", icon: FolderKanban },
      { label: "Hardware", to: "/hardware", icon: Cpu },
      { label: "My Loans", to: "/loans", icon: ArrowLeftRight },
      { label: "Events", to: "/events", icon: CalendarDays },
      { label: "My Events", to: "/my-events", icon: CalendarCheck },
      { label: "News", to: "/articles", icon: Newspaper },
      { label: "Profile", to: "/profile", icon: UserRound },
    ],
  },
  {
    label: "Admin",
    adminOnly: true,
    items: [
      { label: "Overview", to: "/admin", icon: ShieldCheck, exact: true },
      { label: "Loan requests", to: "/admin/loans", icon: ClipboardCheck },
      { label: "Members", to: "/admin/users", icon: Users },
      { label: "Inventory", to: "/admin/hardware", icon: Boxes },
    ],
  },
];
