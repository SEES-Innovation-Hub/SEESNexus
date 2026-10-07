import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { listProjects, type ProjectListParams } from "../api/projects";
import { queryKeys } from "../api/queryKeys";

// One page of projects for the Projects page. While the next page or filter
// loads, the previous results stay on screen (isPlaceholderData is true) instead
// of the grid flashing back to skeletons.
export function useProjectList(params: ProjectListParams) {
  return useQuery({
    queryKey: queryKeys.projects.list(params),
    queryFn: () => listProjects(params),
    placeholderData: keepPreviousData,
  });
}
