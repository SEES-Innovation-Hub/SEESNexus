import { createContext } from "react";
import type { User, UserUpdatePayload } from "../types/auth";

export interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  // The browser-history entry (React Router's location.key) on which the person
  // pressed "Log out", so ProtectedRoute can send that page to Landing. Any other
  // page, or an expired session, still goes to login. null if they didn't.
  loggedOutAt: string | null;
  login: (email: string, password: string) => Promise<User>;
  // Call through useLogout(), which supplies the current page's location.key.
  logout: (locationKey: string) => void;
  updateProfile: (payload: UserUpdatePayload) => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
