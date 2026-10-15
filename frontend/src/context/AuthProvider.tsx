import { useEffect, useState, type ReactNode } from "react";
import * as authApi from "../api/auth";
import { setSessionExpiredHandler } from "../api/client";
import { queryClient } from "../api/queryClient";
import { tokenStore } from "../api/tokenStore";
import type { User, UserUpdatePayload } from "../types/auth";
import { AuthContext } from "./AuthContext";

// Cached API data can include one person's private records (their loans, the
// admin's user list), so it is dropped whenever the signed-in user changes —
// the next person on a shared computer must never see it, even for a moment.
function signOut(setUser: (user: User | null) => void) {
  queryClient.clear();
  setUser(null);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(
    () => tokenStore.getAccess() !== null,
  );

  // Syncs with things outside React on mount: restores a session from a token
  // already in browser storage, and subscribes to the API client's session-expiry
  // signal — neither is derivable from props/state or triggered by a handler.
  useEffect(() => {
    setSessionExpiredHandler(() => signOut(setUser));
    if (tokenStore.getAccess() === null) return;
    // A failure leaves the user signed out; the API client has already
    // cleared the tokens if it was an auth failure.
    authApi
      .getMe()
      .then(setUser)
      .catch(() => undefined)
      .finally(() => setIsLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const tokens = await authApi.login(email, password);
    tokenStore.setBoth(tokens.access_token, tokens.refresh_token);
    const loggedInUser = await authApi.getMe();
    queryClient.clear();
    setUser(loggedInUser);
    return loggedInUser;
  }

  function logout() {
    tokenStore.clear();
    signOut(setUser);
  }

  async function updateProfile(payload: UserUpdatePayload) {
    setUser(await authApi.updateMe(payload));
  }

  return (
    <AuthContext.Provider
      value={{ user, isLoading, login, logout, updateProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
}
