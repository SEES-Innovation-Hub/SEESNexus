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
