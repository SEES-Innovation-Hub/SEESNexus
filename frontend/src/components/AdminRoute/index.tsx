import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { redirectPathForRole } from "../../utils/redirectPathForRole";

// Wraps admin-only pages. Not signed in → /login; signed in but not an admin →
// back to that user's own start page. This is for a clean experience only: the
// backend refuses admin requests from non-admins whatever the frontend does.
export default function AdminRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "ADMIN") return <Navigate to={redirectPathForRole(user.role)} replace />;

  return children;
}
