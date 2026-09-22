import { useEffect, useState } from "react";
import { listProjects } from "../api/projects";
import type { Project } from "../types/project";

export type ProjectsState =
  | { status: "loading" }
  | { status: "error" }
  | { status: "ready"; projects: Project[]; total: number };

type ReadyState = Extract<ProjectsState, { status: "ready" }>;

// The last successful list is kept in the browser so a returning visitor sees
// projects on the very first paint instead of a skeleton. It is only a head start:
// the fresh list from the API always replaces it as soon as it arrives.
// Bump the version if the Project shape changes so old copies are ignored.
const cacheKey = (pageSize: number) => `sees.projects.v1.${pageSize}`;
const MAX_CACHE_AGE_MS = 7 * 24 * 60 * 60 * 1000;

function readCache(pageSize: number): ReadyState | null {
  try {
    const saved = JSON.parse(localStorage.getItem(cacheKey(pageSize)) ?? "null");
    const isUsable =
      saved &&
      Array.isArray(saved.projects) &&
      typeof saved.total === "number" &&
      Date.now() - saved.savedAt < MAX_CACHE_AGE_MS;
    return isUsable ? { status: "ready", projects: saved.projects, total: saved.total } : null;
  } catch {
    // Storage blocked (e.g. private mode) or the saved text isn't valid JSON.
    return null;
  }
}

function writeCache(pageSize: number, state: ReadyState) {
  try {
    const { projects, total } = state;
    localStorage.setItem(cacheKey(pageSize), JSON.stringify({ savedAt: Date.now(), projects, total }));
  } catch {
    // Storage full or blocked: caching is best-effort, the page works without it.
  }
}

export function useProjects(pageSize: number): ProjectsState {
  const [state, setState] = useState<ProjectsState>(
    () => readCache(pageSize) ?? { status: "loading" },
  );

  // Fetching from the API on mount is syncing with an external system; the
  // `ignore` flag drops the result of a stale request (StrictMode remount).
  useEffect(() => {
    let ignore = false;
    listProjects(pageSize)
      .then((page) => {
        const fresh: ReadyState = { status: "ready", projects: page.items, total: page.total };
        writeCache(pageSize, fresh);
        if (!ignore) setState(fresh);
      })
      .catch(() => {
        // A failed refresh must not throw away projects we can already show.
        if (!ignore) setState((current) => (current.status === "ready" ? current : { status: "error" }));
      });
    return () => {
      ignore = true;
    };
  }, [pageSize]);

  return state;
}
