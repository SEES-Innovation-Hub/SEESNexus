import { Plus } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { buttonClassName } from "../../components/Button/buttonClassName";
import Button from "../../components/Button";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import Pagination from "../../components/Pagination";
import PrefetchLink from "../../components/PrefetchLink";
import ProjectCard from "../../components/ProjectCard";
import Select from "../../components/Select";
import Skeleton from "../../components/Skeleton";
import { useAuth } from "../../hooks/useAuth";
import { useProjectList } from "../../hooks/useProjectList";
import {
  CATEGORY_OPTIONS,
  STATUS_OPTIONS,
  isProjectCategory,
  isProjectStatus,
} from "../../utils/projectLabels";

const PAGE_SIZE = 12;

// Filters and the page number live in the address bar (?category=IOT&page=2),
// so Back/Forward and shared links work and no effect is needed to sync them.
export function ProjectsList() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const categoryParam = searchParams.get("category");
  const statusParam = searchParams.get("status");
  const category = isProjectCategory(categoryParam) ? categoryParam : undefined;
  const status = isProjectStatus(statusParam) ? statusParam : undefined;
  const page = Math.max(1, Math.floor(Number(searchParams.get("page"))) || 1);
  const isFiltered = category !== undefined || status !== undefined || page > 1;

  const { data, isPending, isError, isFetching, isPlaceholderData, refetch } = useProjectList({
    page,
    pageSize: PAGE_SIZE,
    category,
    status,
  });

  // Changing a filter starts again from page 1.
  function setParam(name: "category" | "status" | "page", value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(name, value);
    else next.delete(name);
    if (name !== "page") next.delete("page");
    setSearchParams(next);
  }

  function goToPage(nextPage: number) {
    setParam("page", nextPage > 1 ? String(nextPage) : "");
    window.scrollTo({ top: 0 });
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-sees-mint">Projects</h1>
          <p className="mt-1 text-white/60">
            Student work from across SEES
            {data && data.total > 0 && ` · ${data.total} ${data.total === 1 ? "project" : "projects"}`}
          </p>
        </div>
        {user ? (
          <PrefetchLink to="/projects/new" className={buttonClassName()}>
            <Plus aria-hidden="true" className="size-4" />
            New project
          </PrefetchLink>
        ) : (
          <PrefetchLink to="/login" className={buttonClassName("secondary")}>
            Log in to add a project
          </PrefetchLink>
        )}
      </div>

      <div className="grid max-w-xl gap-4 sm:grid-cols-2">
        <Select
          id="filter-category"
          label="Category"
          value={category ?? ""}
          onChange={(value) => setParam("category", value)}
          options={CATEGORY_OPTIONS}
          placeholder="All categories"
          required={false}
        />
        <Select
          id="filter-status"
          label="Status"
          value={status ?? ""}
          onChange={(value) => setParam("status", value)}
          options={STATUS_OPTIONS}
          placeholder="All statuses"
          required={false}
        />
      </div>

      {isPending && (
        <div aria-busy="true" aria-label="Loading projects" className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-80 rounded-2xl" />
          ))}
        </div>
      )}

      {isError && !data && <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />}

      {data && data.items.length === 0 && (
        isFiltered ? (
          <EmptyState
            title="No projects here"
            message="Nothing matches these filters."
            action={
              <Button variant="secondary" onClick={() => setSearchParams({})}>
                Show all projects
              </Button>
            }
          />
        ) : (
          <EmptyState
            title="No projects yet"
            message="Be the first to showcase your work."
            action={
              user && (
                <PrefetchLink to="/projects/new" className={buttonClassName()}>
                  New project
                </PrefetchLink>
              )
            }
          />
        )
      )}

      {data && data.items.length > 0 && (
        <>
          {/* Dimmed while the next page or filter loads over the old results. */}
          <ul
            aria-busy={isPlaceholderData}
            className={`grid gap-5 transition-opacity sm:grid-cols-2 xl:grid-cols-3 ${isPlaceholderData ? "opacity-60" : ""}`}
          >
            {data.items.map((project) => (
              <li key={project.id}>
                <ProjectCard project={project} />
              </li>
            ))}
          </ul>
          <Pagination page={page} totalPages={data.total_pages} onPageChange={goToPage} />
        </>
      )}
    </div>
  );
}
