import { api, unwrap } from "./client";
import type { DashboardStats } from "../types/admin";
import type { User, UserRole } from "../types/auth";
import type { Loan } from "../types/hardware";

// Every /admin route requires an ADMIN token (backend/app/api/v1/admin.py).

export function getAdminStats() {
  return unwrap<DashboardStats>(api.get("/admin/dashboard"));
}

// Newest accounts first; the backend has no paging or search yet.
export function listUsers() {
  return unwrap<User[]>(api.get("/admin/users"));
}

// Making someone an ADMIN needs the admin key (403 "Invalid admin key" otherwise).
export function changeUserRole(userId: string, role: UserRole, adminKey?: string) {
  return unwrap<User>(api.put(`/admin/users/${userId}/role`, { role, admin_key: adminKey }));
}

// Soft delete: the account can no longer log in. activateUser undoes it.
export function deactivateUser(userId: string) {
  return unwrap<null>(api.delete(`/admin/users/${userId}`));
}

export function activateUser(userId: string) {
  return unwrap<User>(api.put(`/admin/users/${userId}/activate`));
}

// Every loan from every member, newest request first.
export function listAllLoans() {
  return unwrap<Loan[]>(api.get("/admin/loans"));
}

// Approving takes a unit off the shelf; fails if none are left.
export function approveLoan(loanId: string) {
  return unwrap<Loan>(api.put(`/admin/loans/${loanId}/approve`));
}

export function rejectLoan(loanId: string) {
  return unwrap<Loan>(api.put(`/admin/loans/${loanId}/reject`));
}

// The item is physically back at the lab: puts the unit back on the shelf.
export function returnLoan(loanId: string) {
  return unwrap<Loan>(api.put(`/admin/loans/${loanId}/return`));
}
