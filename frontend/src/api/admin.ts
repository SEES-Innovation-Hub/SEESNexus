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

export function changeUserRole(userId: string, role: UserRole) {
  return unwrap<User>(api.put(`/admin/users/${userId}/role`, { role }));
}

// Soft delete: the account can no longer log in. There is no undo endpoint yet.
export function deactivateUser(userId: string) {
  return unwrap<null>(api.delete(`/admin/users/${userId}`));
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
