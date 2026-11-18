import { ArrowLeft, CalendarDays, ExternalLink, MapPin, Pencil, RotateCcw, Trash, Users, Video } from "lucide-react";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { errorMessage, isNotFoundError } from "../../api/client";
import Badge from "../../components/Badge";
import Button from "../../components/Button";
import { buttonClassName } from "../../components/Button/buttonClassName";
import Card from "../../components/Card";
import ConfirmDialog from "../../components/ConfirmDialog";
import ErrorState from "../../components/ErrorState";
import PrefetchLink from "../../components/PrefetchLink";
import Skeleton from "../../components/Skeleton";
import { useAuth } from "../../hooks/useAuth";
import { useDeleteEvent, useRestoreEvent } from "../../hooks/useEventActions";
import { useEvent } from "../../hooks/useEvents";
import { useToast } from "../../hooks/useToast";
import { EVENT_TYPE_LABELS, eventWhen, formatDateTime, placesSummary } from "../../utils/eventLabels";
import { isHttpUrl } from "../../utils/isHttpUrl";
import { EventNotFound } from "./EventNotFound";
import { RegistrationPanel } from "./RegistrationPanel";

const backLinkClassName =
  "-my-3 inline-flex items-center gap-1 py-3 text-sm text-sees-mustard hover:text-sees-mint";

export function EventDetail() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  const { showToast } = useToast();
  const navigate = useNavigate();
  const { data: event, error, isPending, isFetching, refetch } = useEvent(id);
  const deleteEvent = useDeleteEvent();
  const restoreEvent = useRestoreEvent();
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  if (isPending) {
    return (
      <div aria-busy="true" aria-label="Loading event" className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-32 rounded-2xl" />
        <Skeleton className="h-9 w-2/3" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }
  if (!event) {
    return isNotFoundError(error) ? <EventNotFound /> : <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />;
  }

  function handleDelete() {
    deleteEvent.mutate(id, {
      onSuccess: () => {
        setConfirmingDelete(false);
        showToast("Event deleted. You can restore it from Events → Deleted.");
        navigate("/events");
      },
      onError: (deleteError) => {
        setConfirmingDelete(false);
        showToast(errorMessage(deleteError, "Couldn't delete the event. Try again."), "error");
      },
    });
  }

  function handleRestore() {
    restoreEvent.mutate(id, {
      onSuccess: () => showToast("Event restored"),
      onError: (restoreError) => showToast(errorMessage(restoreError, "Couldn't restore the event."), "error"),
    });
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PrefetchLink to="/events" className={backLinkClassName}>
        <ArrowLeft aria-hidden="true" className="size-4" />
        All events
      </PrefetchLink>

      <Card as="article" padding="none" className="overflow-hidden">
        {event.banner_url && (
          <img src={event.banner_url} alt="" width={1152} height={480} className="aspect-[12/5] w-full object-cover" />
        )}
        <div className="space-y-6 p-5 sm:p-8">
          {event.deleted_at && (
            <div role="status" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-400/40 bg-red-950/30 p-4">
              <p className="text-sm text-red-200">
                Deleted {formatDateTime(event.deleted_at)}. Members can't see it.
              </p>
              <Button variant="secondary" onClick={handleRestore} isLoading={restoreEvent.isPending}>
                <RotateCcw aria-hidden="true" className="size-4" />
                Restore event
              </Button>
            </div>
          )}

          <div className="space-y-3">
            <Badge tone="mint">{EVENT_TYPE_LABELS[event.event_type]}</Badge>
            <h1 className="text-2xl font-semibold wrap-anywhere text-white sm:text-3xl">{event.title}</h1>
          </div>

          <ul className="space-y-2 text-white/80">
            <li className="flex gap-2">
              <CalendarDays aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-sees-mint/70" />
              <span>{eventWhen(event)}</span>
            </li>
            <li className="flex gap-2">
              {event.is_virtual ? (
                <Video aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-sees-mint/70" />
              ) : (
                <MapPin aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-sees-mint/70" />
              )}
              <span className="wrap-anywhere">
                {event.location}
                {event.is_virtual && !/online/i.test(event.location) && " · online"}
              </span>
            </li>
            <li className="flex gap-2">
              <Users aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-sees-mint/70" />
              <span>{placesSummary(event)}</span>
            </li>
          </ul>

          {!event.deleted_at && <RegistrationPanel event={event} />}

          <p className="whitespace-pre-line wrap-anywhere text-white/80">{event.description}</p>

          {isAdmin && (
            <div className="space-y-4 border-t border-sees-teal/40 pt-6">
              <h2 className="text-sm font-medium text-sees-mint/80">Organiser tools</h2>
              {event.is_virtual && isHttpUrl(event.virtual_link) && (
                <p className="text-sm wrap-anywhere text-white/60">
                  Meeting link:{" "}
                  <a href={event.virtual_link} target="_blank" rel="noreferrer" className="text-sees-mustard underline hover:text-sees-mint">
                    {event.virtual_link}
                    <ExternalLink aria-hidden="true" className="ml-1 inline size-3" />
                  </a>
                </p>
              )}
              <div className="flex flex-wrap gap-3">
                <PrefetchLink to={`/events/${event.id}/participants`} className={buttonClassName("secondary")}>
                  <Users aria-hidden="true" className="size-4" />
                  Participants & attendance
                </PrefetchLink>
                {!event.deleted_at && (
                  <>
                    <PrefetchLink to={`/events/${event.id}/edit`} className={buttonClassName()}>
                      <Pencil aria-hidden="true" className="size-4" />
                      Edit event
                    </PrefetchLink>
                    <Button variant="danger" onClick={() => setConfirmingDelete(true)}>
                      <Trash aria-hidden="true" className="size-4" />
                      Delete
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </Card>

      <ConfirmDialog
        open={confirmingDelete}
        title="Delete this event?"
        message={`"${event.title}" will disappear for members. Registrations are kept, and you can restore it later from Events → Deleted.`}
        confirmLabel="Delete event"
        onConfirm={handleDelete}
        onCancel={() => setConfirmingDelete(false)}
        isPending={deleteEvent.isPending}
      />
    </div>
  );
}
