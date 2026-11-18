import { buttonClassName } from "../../components/Button/buttonClassName";
import EmptyState from "../../components/EmptyState";
import PrefetchLink from "../../components/PrefetchLink";

// Shown when the event doesn't exist (deleted, or a mistyped link).
export function EventNotFound() {
  return (
    <EmptyState
      title="Event not found"
      message="It may have been cancelled by the organisers, or the link is wrong."
      action={
        <PrefetchLink to="/events" className={buttonClassName("secondary")}>
          Browse events
        </PrefetchLink>
      }
    />
  );
}
