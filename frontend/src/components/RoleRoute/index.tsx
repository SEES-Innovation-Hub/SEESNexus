import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import type { UserRole } from "../../types/auth";
import { redirectPathForRole } from "../../utils/redirectPathForRole";

// Wraps pages only some roles may open. Not signed in → /login; signed in with
// another role → back to that user's own start page. This is for a clean
// experience only: the backend refuses the requests whatever the frontend does.
export default function RoleRoute({ roles, children }: { roles: readonly UserRole[]; children: ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <Navigate to={redirectPathForRole(user.role)} replace />;

  return children;
}
