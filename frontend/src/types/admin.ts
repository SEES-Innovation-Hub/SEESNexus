// Mirrors backend/app/schemas/admin.py — keep in sync with the backend.
export interface DashboardStats {
  total_users: number;
  active_users: number;
  students: number;
  contributors: number;
  admins: number;
  total_projects: number;
  total_events: number;
  total_articles: number;
  total_hardware_items: number;
  pending_loans: number;
  approved_loans: number;
}
