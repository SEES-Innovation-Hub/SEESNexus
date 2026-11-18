import ErrorState from "../../components/ErrorState";
import PrefetchLink from "../../components/PrefetchLink";
import Skeleton from "../../components/Skeleton";
import { useEventList, useMyRegistrations } from "../../hooks/useEvents";
import type { RegistrationStatus } from "../../types/events";
import { EventCard } from "../events/EventCard";

const COUNT = 3;

// The next few events, with the member's own status on each.
export function UpcomingEvents() {
  const { data, isPending, isError, isFetching, refetch } = useEventList({ page: 1, pageSize: COUNT, upcoming: true });
  const mine = useMyRegistrations();
  const myStatus = new Map<string, RegistrationStatus>(
    (mine.data ?? []).filter((r) => r.status !== "CANCELLED").map((r) => [r.event_id, r.status]),
  );

  return (
    <section aria-labelledby="upcoming-events-heading" className="space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="upcoming-events-heading" className="text-xl font-medium text-white">
          Upcoming events
        </h2>
        <PrefetchLink to="/events" className="-my-3 py-3 text-sm text-sees-mustard underline hover:text-sees-mint">
          All events
        </PrefetchLink>
      </div>
      {isPending && (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: COUNT }, (_, index) => (
            <Skeleton key={index} className="h-56 rounded-2xl" />
          ))}
        </div>
      )}
      {isError && <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />}
      {data && data.items.length === 0 && <p className="text-sm text-white/50">Nothing scheduled yet.</p>}
      {data && data.items.length > 0 && (
        <ul className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {data.items.map((event) => (
            <li key={event.id}>
              <EventCard event={event} myStatus={myStatus.get(event.id)} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
