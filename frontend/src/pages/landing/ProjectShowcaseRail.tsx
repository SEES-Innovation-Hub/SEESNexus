import { useRef } from "react";
import PrefetchLink from "../../components/PrefetchLink";
import ProjectCard from "../../components/ProjectCard";
import { useShowcaseProjects } from "../../hooks/useShowcaseProjects";

const RAIL_SIZE = 12;
const SKELETON_COUNT = 3;

// Phones swipe the rail; the arrows are for tablet/desktop pointers (44px targets).
const arrowClassName =
  "flex size-11 items-center justify-center rounded-full border border-sees-teal text-sees-mint hover:border-sees-mint";

export function ProjectShowcaseRail() {
  const state = useShowcaseProjects(RAIL_SIZE);
  const railRef = useRef<HTMLDivElement>(null);

  function scrollRail(direction: 1 | -1) {
    const rail = railRef.current;
    rail?.scrollBy({ left: direction * rail.clientWidth * 0.8, behavior: "smooth" });
  }

  const hasProjects = state.status === "ready" && state.projects.length > 0;

  return (
    <section
      id="projects"
      aria-labelledby="projects-heading"
      className="mx-auto w-full max-w-6xl px-6 py-16"
    >
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 id="projects-heading" className="text-3xl font-semibold text-sees-mint">
            Innovation Gallery
          </h2>
          <p className="mt-2 text-white/70">
            Latest student work from across SEES.
            {state.status === "ready" && state.total > 0 && (
              <span className="block font-mono text-sm text-sees-mint sm:ml-2 sm:inline">
                {state.total} {state.total === 1 ? "project" : "projects"} showcased
              </span>
            )}
          </p>
          <PrefetchLink
            to="/projects"
            className="-my-3 mt-1 inline-block py-3 text-sm text-sees-mustard underline hover:text-sees-mint"
          >
            View all projects
          </PrefetchLink>
        </div>
        {hasProjects && (
          <div className="hidden gap-2 md:flex">
            <button type="button" aria-label="Scroll projects left" onClick={() => scrollRail(-1)} className={arrowClassName}>
              ‹
            </button>
            <button type="button" aria-label="Scroll projects right" onClick={() => scrollRail(1)} className={arrowClassName}>
              ›
            </button>
          </div>
        )}
      </div>

      {state.status === "loading" && (
        <div aria-hidden="true" className="flex gap-5 overflow-hidden px-2 py-6">
          {Array.from({ length: SKELETON_COUNT }, (_, index) => (
            <div
              key={index}
              className="h-80 w-72 shrink-0 animate-pulse rounded-2xl border border-sees-teal/40 bg-sees-glass"
            />
          ))}
        </div>
      )}

      {state.status === "error" && (
        <p role="alert" className="py-10 text-white/60">
          Couldn't load projects right now. Please try again shortly.
        </p>
      )}

      {state.status === "ready" && state.projects.length === 0 && (
        <p className="py-10 text-white/60">No projects yet — check back soon.</p>
      )}

      {hasProjects && (
        <div
          ref={railRef}
          tabIndex={0}
          role="region"
          aria-label="Latest projects"
          className="flex snap-x snap-mandatory gap-5 overflow-x-auto px-2 py-6 focus-visible:outline-2 focus-visible:outline-sees-mint"
        >
          {state.projects.map((project) => (
            <div
              key={project.id}
              className="w-72 shrink-0 snap-start transition-transform duration-200 focus-within:z-10 focus-within:scale-105 hover:z-10 hover:scale-105"
            >
              <ProjectCard project={project} />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
