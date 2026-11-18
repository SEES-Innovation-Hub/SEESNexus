import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createProject } from "../api/projects";
import { queryKeys } from "../api/queryKeys";

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      // The detail page opened next has its data already; lists refetch in the
      // background (not awaited, so navigation isn't held up).
      queryClient.setQueryData(queryKeys.projects.detail(project.id), project);
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.lists });
    },
  });
}
