import { Plus } from "lucide-react";
import Button from "../../components/Button";
import { buttonClassName } from "../../components/Button/buttonClassName";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import Pagination from "../../components/Pagination";
import PrefetchLink from "../../components/PrefetchLink";
import Select from "../../components/Select";
import Skeleton from "../../components/Skeleton";
import { useAuth } from "../../hooks/useAuth";
import { useEventList, useMyRegistrations } from "../../hooks/useEvents";
import { useUrlFilters } from "../../hooks/useUrlFilters";
import type { RegistrationStatus } from "../../types/events";
import { EVENT_TYPE_OPTIONS, isEventType } from "../../utils/eventLabels";
import { EventCard } from "./EventCard";

const PAGE_SIZE = 12;

const VIEWS = {
  upcoming: "Upcoming",
  all: "All events",
  deleted: "Deleted",
} as const;
type View = keyof typeof VIEWS;

function isView(value: string | null): value is View {
  return value !== null && Object.hasOwn(VIEWS, value);
}

export function EventsList() {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  const { page, read, setFilter, setPage, clearAll } = useUrlFilters();
  const eventType = read("type", isEventType);
  // Deleted events are an admin view; anyone else asking gets the default.
  const requested = read("view", isView) ?? "upcoming";
  const view: View = requested === "deleted" && !isAdmin ? "upcoming" : requested;

  const { data, isPending, isError, isFetching, isPlaceholderData, refetch } = useEventList({
    page,
    pageSize: PAGE_SIZE,
    eventType,
    upcoming: view === "upcoming",
    deleted: view === "deleted",
  });
  const mine = useMyRegistrations();
  const myStatus = new Map<string, RegistrationStatus>(
    (mine.data ?? [])
      .filter((registration) => registration.status !== "CANCELLED")
      .map((registration) => [registration.event_id, registration.status]),
  );

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-sees-mint">Events</h1>
          <p className="mt-1 text-white/60">Hackathons, workshops, seminars and orientations across SEES.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <PrefetchLink to="/my-events" className={buttonClassName("secondary")}>
            My events
          </PrefetchLink>
          {isAdmin && (
            <PrefetchLink to="/events/new" className={buttonClassName()}>
              <Plus aria-hidden="true" className="size-4" />
              New event
            </PrefetchLink>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-4">
        <div role="group" aria-label="Show" className="flex flex-wrap gap-2">
          {(Object.keys(VIEWS) as View[])
            .filter((key) => key !== "deleted" || isAdmin)
            .map((key) => (
              <button
                key={key}
                type="button"
                aria-pressed={view === key}
                onClick={() => setFilter("view", key === "upcoming" ? "" : key)}
                className={`inline-flex min-h-11 items-center rounded-full border px-4 text-sm font-medium transition-colors ${
                  view === key
                    ? "border-sees-mint bg-sees-mint/10 text-sees-mint"
                    : "border-sees-teal text-white/70 hover:border-sees-mint/60 hover:text-white"
                }`}
              >
                {VIEWS[key]}
              </button>
            ))}
        </div>
        <div className="w-full sm:w-56">
          <Select
            id="filter-type"
            label="Type"
            value={eventType ?? ""}
            onChange={(value) => setFilter("type", value)}
            options={EVENT_TYPE_OPTIONS}
            placeholder="All types"
            required={false}
          />
        </div>
      </div>

      {isPending && (
        <div aria-busy="true" aria-label="Loading events" className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-64 rounded-2xl" />
          ))}
        </div>
      )}
      {isError && !data && <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />}

      {data && data.items.length === 0 && (
        <EmptyState
          title={view === "deleted" ? "No deleted events" : "No events here"}
          message={
            view === "upcoming" && !eventType
              ? "Nothing is scheduled yet. Check back soon."
              : "Nothing matches these filters."
          }
          action={
            view !== "upcoming" || eventType ? (
              <Button variant="secondary" onClick={clearAll}>
                Show upcoming events
              </Button>
            ) : undefined
          }
        />
      )}

      {data && data.items.length > 0 && (
        <>
          <ul
            aria-busy={isPlaceholderData}
            className={`grid gap-5 transition-opacity sm:grid-cols-2 xl:grid-cols-3 ${isPlaceholderData ? "opacity-60" : ""}`}
          >
            {data.items.map((event) => (
              <li key={event.id}>
                <EventCard event={event} myStatus={myStatus.get(event.id)} />
              </li>
            ))}
          </ul>
          <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
