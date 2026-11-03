import type { User } from "../types/auth";
import type { Project } from "../types/project";

// Mirrors the backend's rule (backend/app/api/v1/projects.py, _assert_can_edit):
// the creator or an admin may edit or delete a project. The frontend uses it
// only to decide what to show; the backend enforces it.
export function canEditProject(project: Project, user: User | null): boolean {
  return user !== null && (project.created_by_id === user.id || user.role === "ADMIN");
}
