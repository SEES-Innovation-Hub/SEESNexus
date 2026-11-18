import { useLocation } from "react-router-dom";
import { useAuth } from "./useAuth";

// What a "Log out" button calls. It tells the session which page the person
// was on, so ProtectedRoute sends exactly that page to Landing (see AuthContext).
export function useLogout() {
  const { logout } = useAuth();
  const location = useLocation();
  return () => logout(location.key);
}
