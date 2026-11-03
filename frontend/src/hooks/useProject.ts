import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getProject } from "../api/projects";
import { queryKeys } from "../api/queryKeys";
import type { PaginatedProjects } from "../types/project";

// One project. Opening it from a list shows the list's copy straight away (list
// items carry the full record) while the fresh one loads in the background.
export function useProject(id: string) {
  const queryClient = useQueryClient();
  return useQuery({
    queryKey: queryKeys.projects.detail(id),
    queryFn: () => getProject(id),
    placeholderData: () =>
      queryClient
        .getQueriesData<PaginatedProjects>({ queryKey: queryKeys.projects.lists })
        .flatMap(([, page]) => page?.items ?? [])
        .find((project) => project.id === id),
  });
}
