import type { ArticleListParams } from "./articles";
import type { EventListParams } from "./events";
import type { HardwareListParams } from "./hardware";
import type { ProjectListParams } from "./projects";

// Every cached API read is named here, so a screen that changes data can
// refresh exactly the lists it affected, e.g. after creating a project:
//   queryClient.invalidateQueries({ queryKey: queryKeys.projects.lists })
// Keys are nested arrays: invalidating ["projects"] also refreshes every
// ["projects", "list", ...] and ["projects", "detail", ...] entry under it.
export const queryKeys = {
  projects: {
    all: ["projects"] as const,
    lists: ["projects", "list"] as const,
    list: (params: ProjectListParams) => ["projects", "list", params] as const,
    detail: (id: string) => ["projects", "detail", id] as const,
  },
  hardware: {
    lists: ["hardware", "list"] as const,
    list: (params: HardwareListParams) => ["hardware", "list", params] as const,
    detail: (id: string) => ["hardware", "detail", id] as const,
  },
  loans: {
    mine: ["loans", "mine"] as const,
  },
  events: {
    all: ["events"] as const,
    lists: ["events", "list"] as const,
    list: (params: EventListParams) => ["events", "list", params] as const,
    detail: (id: string) => ["events", "detail", id] as const,
    mine: ["events", "mine"] as const,
    participants: (id: string) => ["events", "participants", id] as const,
  },
  articles: {
    all: ["articles"] as const,
    lists: ["articles", "list"] as const,
    list: (params: ArticleListParams) => ["articles", "list", params] as const,
    detail: (idOrSlug: string) => ["articles", "detail", idOrSlug] as const,
  },
  admin: {
    stats: ["admin", "stats"] as const,
    users: ["admin", "users"] as const,
    loans: ["admin", "loans"] as const,
  },
};
