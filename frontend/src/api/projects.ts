import { api, unwrap } from "./client";
import type { PaginatedProjects, ProjectCategory, ProjectStatus } from "../types/project";

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
