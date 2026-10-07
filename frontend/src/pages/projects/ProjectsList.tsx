import { Plus } from "lucide-react";
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
import { useUrlFilters } from "../../hooks/useUrlFilters";
import {
  CATEGORY_OPTIONS,
  STATUS_OPTIONS,
  isProjectCategory,
  isProjectStatus,
} from "../../utils/projectLabels";

const PAGE_SIZE = 12;

export function ProjectsList() {
  const { user } = useAuth();
  const { page, isFiltered, read, setFilter, setPage, clearAll } = useUrlFilters();
  const category = read("category", isProjectCategory);
  const status = read("status", isProjectStatus);

  const { data, isPending, isError, isFetching, isPlaceholderData, refetch } = useProjectList({
    page,
    pageSize: PAGE_SIZE,
    category,
    status,
  });

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
          onChange={(value) => setFilter("category", value)}
          options={CATEGORY_OPTIONS}
          placeholder="All categories"
          required={false}
        />
        <Select
          id="filter-status"
          label="Status"
          value={status ?? ""}
          onChange={(value) => setFilter("status", value)}
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
              <Button variant="secondary" onClick={clearAll}>
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
          <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
