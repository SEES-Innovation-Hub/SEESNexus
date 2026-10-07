import { api, unwrap } from "./client";
import type {
  PaginatedProjects,
  Project,
  ProjectCategory,
  ProjectPayload,
  ProjectStatus,
} from "../types/project";

// Query parameters GET /projects accepts (backend/app/api/v1/projects.py).
export interface ProjectListParams {
  page?: number;
  pageSize?: number;
  category?: ProjectCategory;
  status?: ProjectStatus;
}

// Public endpoint, newest first.
export function listProjects({ page, pageSize, category, status }: ProjectListParams = {}) {
  return unwrap<PaginatedProjects>(
    api.get("/projects", { params: { page, page_size: pageSize, category, status } }),
  );
}

// Public endpoint.
export function getProject(id: string) {
  return unwrap<Project>(api.get(`/projects/${id}`));
}

// Any signed-in user.
export function createProject(payload: ProjectPayload) {
  return unwrap<Project>(api.post("/projects", payload));
}

// Creator or admin only (403 otherwise).
export function updateProject(id: string, payload: ProjectPayload) {
  return unwrap<Project>(api.put(`/projects/${id}`, payload));
}

// Creator or admin only (403 otherwise).
export function deleteProject(id: string) {
  return unwrap<null>(api.delete(`/projects/${id}`));
}
