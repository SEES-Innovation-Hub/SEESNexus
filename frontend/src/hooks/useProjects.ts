import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listProjects } from "../api/projects";
import { queryKeys } from "../api/queryKeys";
import type { PaginatedProjects, Project } from "../types/project";

export type ProjectsState =
  | { status: "loading" }
  | { status: "error" }
  | { status: "ready"; projects: Project[]; total: number };

// The last successful list is kept in the browser so a returning visitor sees
// projects on the very first paint instead of a skeleton. It is only a head start:
// it is handed to the query as already-stale data, so the fresh list from the API
// is fetched straight away and replaces it as soon as it arrives.
// Bump the version if the Project shape changes so old copies are ignored.
const cacheKey = (pageSize: number) => `sees.projects.v2.${pageSize}`;
const MAX_CACHE_AGE_MS = 7 * 24 * 60 * 60 * 1000;

interface SavedPage {
  savedAt: number;
  page: PaginatedProjects;
}

function readCache(pageSize: number): SavedPage | undefined {
  try {
    const saved = JSON.parse(localStorage.getItem(cacheKey(pageSize)) ?? "null");
    const isUsable =
      saved &&
      Array.isArray(saved.page?.items) &&
      typeof saved.page?.total === "number" &&
      Date.now() - saved.savedAt < MAX_CACHE_AGE_MS;
    return isUsable ? saved : undefined;
  } catch {
    // Storage blocked (e.g. private mode) or the saved text isn't valid JSON.
    return undefined;
  }
}

function writeCache(pageSize: number, page: PaginatedProjects) {
  try {
    const saved: SavedPage = { savedAt: Date.now(), page };
    localStorage.setItem(cacheKey(pageSize), JSON.stringify(saved));
  } catch {
    // Storage full or blocked: caching is best-effort, the page works without it.
  }
}

// The newest `pageSize` projects, for the Landing showcase rail.
export function useProjects(pageSize: number): ProjectsState {
  // Read once per mount: parsing storage on every render would be wasted work.
  const [saved] = useState(() => readCache(pageSize));
  const query = useQuery({
    queryKey: queryKeys.projects.list({ pageSize }),
    queryFn: async () => {
      const page = await listProjects({ pageSize });
      writeCache(pageSize, page);
      return page;
    },
    initialData: saved?.page,
    // Marks the saved copy with its real age, so it counts as stale and the
    // query refreshes it immediately instead of trusting it for 30s.
    initialDataUpdatedAt: saved?.savedAt,
  });

  // A failed refresh keeps the projects we can already show (TanStack keeps
  // `data` on error), so "error" only appears when there is nothing to show.
  if (query.data) {
    return { status: "ready", projects: query.data.items, total: query.data.total };
  }
  return query.isError ? { status: "error" } : { status: "loading" };
}
