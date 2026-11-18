import { api, unwrap } from "./client";
import type { ProjectMember } from "../types/project";

// Signed in. Active members whose name contains `q`, at most 10, by name. Only
// id, name and photo come back (backend/app/api/v1/users.py).
export function searchUsers(q: string) {
  return unwrap<ProjectMember[]>(api.get("/users/search", { params: { q } }));
}
