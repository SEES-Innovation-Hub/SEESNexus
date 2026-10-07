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
};
