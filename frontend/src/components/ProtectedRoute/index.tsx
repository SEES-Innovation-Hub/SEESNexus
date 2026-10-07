import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return null;
  // Remembers the page they wanted, so login can bring them back to it.
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;

  return children;
}
