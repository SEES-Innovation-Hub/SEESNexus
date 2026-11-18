import ErrorState from "../../components/ErrorState";
import PrefetchLink from "../../components/PrefetchLink";
import ProjectCard from "../../components/ProjectCard";
import Skeleton from "../../components/Skeleton";
import { useProjectList } from "../../hooks/useProjectList";

const COUNT = 3;

// The newest projects, so members see what others are building.
export function LatestProjects() {
  const { data, isPending, isError, isFetching, refetch } = useProjectList({ page: 1, pageSize: COUNT });

  return (
    <section aria-labelledby="latest-projects-heading" className="space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="latest-projects-heading" className="text-xl font-medium text-white">
          Latest projects
        </h2>
        <PrefetchLink to="/projects" className="-my-3 py-3 text-sm text-sees-mustard underline hover:text-sees-mint">
          All projects
        </PrefetchLink>
      </div>

      {isPending && (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: COUNT }, (_, index) => (
            <Skeleton key={index} className="h-72 rounded-2xl" />
          ))}
        </div>
      )}
      {isError && <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />}
      {data && data.items.length === 0 && (
        <p className="text-sm text-white/50">No projects yet. Be the first to share one.</p>
      )}
      {data && data.items.length > 0 && (
        <ul className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {data.items.map((project) => (
            <li key={project.id}>
              <ProjectCard project={project} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
