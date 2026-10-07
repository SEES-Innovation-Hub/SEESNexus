import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteProject } from "../api/projects";
import { queryKeys } from "../api/queryKeys";

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteProject,
    onSuccess: (_data, id) => {
      queryClient.removeQueries({ queryKey: queryKeys.projects.detail(id) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.lists });
    },
  });
}
