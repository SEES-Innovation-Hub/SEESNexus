import type { UserRole } from "../types/auth";

export const ROLE_LABELS: Record<UserRole, string> = {
  STUDENT: "Student",
  CONTRIBUTOR: "Contributor",
  ADMIN: "Admin",
};

export const ROLE_OPTIONS = Object.entries(ROLE_LABELS).map(([value, label]) => ({
  value: value as UserRole,
  label,
}));
