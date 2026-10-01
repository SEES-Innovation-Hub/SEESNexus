import type { UserRole } from '../types/auth'

// Per Master Task Doc §3.1: "successful login redirects by role."
// Admins land on the admin panel; everyone else lands on their profile.
export function redirectPathForRole(role: UserRole): string {
  return role === 'ADMIN' ? '/admin' : '/profile'
}
