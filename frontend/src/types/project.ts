export type ProjectStatus = "IDEATION" | "IN_PROGRESS" | "COMPLETED";
export type ProjectCategory = "IOT" | "AI_ML" | "EMBEDDED" | "WEB" | "MOBILE";

// Mirrors backend/app/schemas/project.py — keep in sync with the backend.
export interface ProjectMember {
  id: string;
  full_name: string;
  profile_image_url: string | null;
}

export interface Project {
  id: string;
  title: string;
  description: string;
  tech_stack: string[];
  github_url: string | null;
  demo_url: string | null;
  status: ProjectStatus;
  category: ProjectCategory;
  thumbnail_url: string | null;
  created_by_id: string;
  members: ProjectMember[];
  created_at: string;
  updated_at: string;
}

// The body of POST /projects and PUT /projects/:id (ProjectCreateRequest /
// ProjectUpdateRequest). member_ids replaces the whole member list when sent.
export interface ProjectPayload {
  title: string;
  description: string;
  tech_stack: string[];
  category: ProjectCategory;
  status: ProjectStatus;
  github_url: string | null;
  demo_url: string | null;
  member_ids?: string[];
}

export interface PaginatedProjects {
  items: Project[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}
