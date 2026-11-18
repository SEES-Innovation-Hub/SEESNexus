import { api, unwrap } from "./client";
import type {
  RegisterPayload,
  TokenPair,
  User,
  UserUpdatePayload,
} from "../types/auth";

export function sendCode(email: string) {
  return unwrap<{ email: string; debug_code?: string }>(
    api.post("/notify/send-code", { email }),
  );
}

export function verifyCode(email: string, code: string) {
  return unwrap<null>(api.post("/notify/verify-code", { email, code }));
}

export function register(payload: RegisterPayload) {
  return unwrap<User>(api.post("/auth/register", payload));
}

// 403 with "Invalid admin key" (or "not enabled") when it won't work. Checked
// before the email code is sent, because verifying the code uses it up.
export function checkAdminKey(adminKey: string) {
  return unwrap<null>(api.post("/auth/admin-key/check", { admin_key: adminKey }));
}

// Always answers the same, whether or not the address has an account.
export function forgotPassword(email: string) {
  return unwrap<{ email: string; debug_code?: string }>(api.post("/auth/forgot-password", { email }));
}

// 400 with the reason (wrong, expired, or too many tries). Signs out every
// existing session for the account.
export function resetPassword(email: string, code: string, newPassword: string) {
  return unwrap<null>(api.post("/auth/reset-password", { email, code, new_password: newPassword }));
}

export function login(email: string, password: string) {
  return unwrap<TokenPair>(api.post("/auth/login", { email, password }));
}

export function getMe() {
  return unwrap<User>(api.get("/auth/me"));
}

export function updateMe(payload: UserUpdatePayload) {
  return unwrap<User>(api.put("/auth/me", payload));
}
