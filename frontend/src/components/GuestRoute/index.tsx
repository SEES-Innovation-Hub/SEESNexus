import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { redirectPathForRole } from "../../utils/redirectPathForRole";
import { readReturnPath } from "../../utils/returnPath";

// Wraps the pages meant for visitors (Landing, Login, Register). A signed-in
// member is taken into the app instead: to the page a login was for, if any,
// otherwise their home page. They see Landing again only after logging out.
export default function GuestRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  // A stored session is still being checked; showing Landing first would flash.
  if (isLoading) return null;
  if (user) {
    return <Navigate to={readReturnPath(location.state) ?? redirectPathForRole(user.role)} replace />;
  }

  return children;
}
