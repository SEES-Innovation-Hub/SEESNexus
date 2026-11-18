import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading, loggedOutAt } = useAuth();
  const location = useLocation();

  if (isLoading) return null;
  if (!user) {
    // The page where "Log out" was pressed goes to Landing. Anything else (a
    // visitor, an expired session, a later click on a members-only link) goes
    // to login, which remembers the page they wanted.
    return loggedOutAt !== null && loggedOutAt === location.key ? (
      <Navigate to="/" replace />
    ) : (
      <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
    );
  }

  return children;
}
