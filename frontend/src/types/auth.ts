export type UserRole = "STUDENT" | "CONTRIBUTOR" | "ADMIN";

// Mirrors app/schemas/auth.py::UserPublic — keep in sync with the backend.
export interface User {
  id: string;
  full_name: string;
  email: string;
  department: string;
  level: string | null;
  role: UserRole;
  profile_image_url: string | null;
  bio: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterPayload {
  full_name: string;
  email: string;
  password: string;
  department: string;
  level: string;
  verification_code: string;
}

export interface UserUpdatePayload {
  full_name?: string;
  department?: string;
  level?: string;
  bio?: string;
  profile_image_url?: string;
}
