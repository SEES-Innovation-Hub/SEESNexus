import type { UserRole } from '../types/auth'

// A signed-in member's home: where login lands and where the logo goes.
// Per Master Task Doc §3.1, "successful login redirects by role": admins get
// the admin overview, everyone else their Dashboard.
export function redirectPathForRole(role: UserRole): string {
  return role === 'ADMIN' ? '/admin' : '/dashboard'
}
