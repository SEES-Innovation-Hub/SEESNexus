import type { Project, ProjectCategory, ProjectMember, ProjectPayload, ProjectStatus } from "../../types/project";
import { isHttpUrl } from "../../utils/isHttpUrl";

// What the form edits: text inputs hold strings, so empty links are "" here and
// become null in the payload; category is "" until one is picked.
export interface ProjectFormValues {
  title: string;
  description: string;
  category: ProjectCategory | "";
  status: ProjectStatus;
  techStack: string[];
  githubUrl: string;
  demoUrl: string;
  // The whole team; sent as member_ids, which replaces the team on save.
  members: ProjectMember[];
}

export type ProjectFormErrors = Partial<Record<keyof ProjectFormValues, string>>;

// Limits match the backend's schema (backend/app/schemas/project.py).
export const TITLE_MAX = 255;
export const URL_MAX = 500;
export const TECH_MAX_ITEMS = 20;
export const TECH_MAX_LENGTH = 50;

export const EMPTY_VALUES: ProjectFormValues = {
  title: "",
  description: "",
  category: "",
  status: "IDEATION",
  techStack: [],
  githubUrl: "",
  demoUrl: "",
  members: [],
};

export function toFormValues(project: Project): ProjectFormValues {
  return {
    title: project.title,
    description: project.description,
    category: project.category,
    status: project.status,
    techStack: project.tech_stack,
    githubUrl: project.github_url ?? "",
    demoUrl: project.demo_url ?? "",
    members: project.members,
  };
}

function validateUrl(value: string): string | undefined {
  if (value === "") return undefined;
  if (!isHttpUrl(value)) return "Enter a full link starting with https://";
  if (value.length > URL_MAX) return `Keep the link under ${URL_MAX} characters.`;
  return undefined;
}

// Checked in the browser first so people get a clear message per field; the
// backend runs the same checks and would only answer "Validation failed".
export function validate(values: ProjectFormValues): ProjectFormErrors {
  const errors: ProjectFormErrors = {
    title: values.title.trim() ? undefined : "Give the project a title.",
    description: values.description.trim() ? undefined : "Describe the project in a sentence or two.",
    category: values.category ? undefined : "Pick a category.",
    githubUrl: validateUrl(values.githubUrl.trim()),
    demoUrl: validateUrl(values.demoUrl.trim()),
  };
  return Object.fromEntries(Object.entries(errors).filter(([, message]) => message)) as ProjectFormErrors;
}

// Only call after validate() returned no errors (category is then set).
export function toPayload(values: ProjectFormValues): ProjectPayload {
  return {
    title: values.title.trim(),
    description: values.description.trim(),
    category: values.category as ProjectCategory,
    status: values.status,
    tech_stack: values.techStack,
    github_url: values.githubUrl.trim() || null,
    demo_url: values.demoUrl.trim() || null,
    member_ids: values.members.map((member) => member.id),
  };
}
