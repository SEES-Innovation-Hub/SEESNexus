import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateProject } from "../api/projects";
import { queryKeys } from "../api/queryKeys";
import type { ProjectPayload } from "../types/project";

export function useUpdateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ProjectPayload }) => updateProject(id, payload),
    onSuccess: (project) => {
      queryClient.setQueryData(queryKeys.projects.detail(project.id), project);
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.lists });
    },
  });
}
