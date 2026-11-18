import type { UserRole } from '../types/auth'

// A signed-in member's home: where login lands and where the logo goes.
// Per Master Task Doc §3.1, "successful login redirects by role". Until the
// Dashboard (everyone) and the admin overview (admins) exist in Phase 3, every
// role lands on Projects, the page with the most to see.
export function redirectPathForRole(_role: UserRole): string {
  return '/projects'
}
