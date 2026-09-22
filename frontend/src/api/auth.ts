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

export function login(email: string, password: string) {
  return unwrap<TokenPair>(api.post("/auth/login", { email, password }));
}

export function getMe() {
  return unwrap<User>(api.get("/auth/me"));
}

export function updateMe(payload: UserUpdatePayload) {
  return unwrap<User>(api.put("/auth/me", payload));
}
