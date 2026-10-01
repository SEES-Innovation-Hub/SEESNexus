import { api, unwrap } from "./client";
import type { PaginatedProjects } from "../types/project";

// Public endpoint, newest first; the first page is all any caller needs so far.
export function listProjects(pageSize: number) {
  return unwrap<PaginatedProjects>(
    api.get("/projects", { params: { page_size: pageSize } }),
  );
}
