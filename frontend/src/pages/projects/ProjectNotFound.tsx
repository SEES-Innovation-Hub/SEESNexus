import { buttonClassName } from "../../components/Button/buttonClassName";
import EmptyState from "../../components/EmptyState";
import PrefetchLink from "../../components/PrefetchLink";

// Shown by the detail and edit pages when the project doesn't exist (a deleted
// project, or a mistyped link).
export function ProjectNotFound() {
  return (
    <EmptyState
      title="Project not found"
      message="It may have been deleted, or the link is wrong."
      action={
        <PrefetchLink to="/projects" className={buttonClassName("secondary")}>
          Browse projects
        </PrefetchLink>
      }
    />
  );
}
