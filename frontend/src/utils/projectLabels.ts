import type { ProjectCategory, ProjectStatus } from "../types/project";

export const CATEGORY_LABELS: Record<ProjectCategory, string> = {
  IOT: "IoT",
  AI_ML: "AI / ML",
  EMBEDDED: "Embedded",
  WEB: "Web",
  MOBILE: "Mobile",
};

export const STATUS_LABELS: Record<ProjectStatus, string> = {
  IDEATION: "Ideation",
  IN_PROGRESS: "In progress",
  COMPLETED: "Completed",
};

// For <Select options>: the same values and labels as above, in display order.
export const CATEGORY_OPTIONS = Object.entries(CATEGORY_LABELS).map(([value, label]) => ({
  value: value as ProjectCategory,
  label,
}));

export const STATUS_OPTIONS = Object.entries(STATUS_LABELS).map(([value, label]) => ({
  value: value as ProjectStatus,
  label,
}));

// Filters come from the address bar, so anything can be typed there; unknown
// values are treated as "no filter" instead of being sent to the API.
export function isProjectCategory(value: string | null): value is ProjectCategory {
  return value !== null && Object.hasOwn(CATEGORY_LABELS, value);
}

export function isProjectStatus(value: string | null): value is ProjectStatus {
  return value !== null && Object.hasOwn(STATUS_LABELS, value);
}
