import { createContext } from "react";
import type { User, UserUpdatePayload } from "../types/auth";

export interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  updateProfile: (payload: UserUpdatePayload) => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
