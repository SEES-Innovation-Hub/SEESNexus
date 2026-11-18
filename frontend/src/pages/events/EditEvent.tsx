import { useNavigate, useParams } from "react-router-dom";
import { errorMessage, isNotFoundError } from "../../api/client";
import Card from "../../components/Card";
import ErrorState from "../../components/ErrorState";
import Skeleton from "../../components/Skeleton";
import { useUpdateEvent } from "../../hooks/useEventActions";
import { useEvent } from "../../hooks/useEvents";
import { useToast } from "../../hooks/useToast";
import { toFormValues } from "./eventFormValues";
import { EventForm } from "./EventForm";
import { EventNotFound } from "./EventNotFound";

export function EditEvent() {
  const { id = "" } = useParams();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const { data: event, error, isPending, isFetching, refetch } = useEvent(id);
  const updateEvent = useUpdateEvent();

  if (isPending) {
    return (
      <div aria-busy="true" aria-label="Loading event" className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-9 w-48" />
        <Skeleton className="h-96 rounded-2xl" />
      </div>
    );
  }
  if (!event || event.deleted_at) {
    return isNotFoundError(error) || event?.deleted_at ? (
      <EventNotFound />
    ) : (
      <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">Edit event</h1>
        <p className="mt-1 wrap-anywhere text-white/60">{event.title}</p>
      </div>
      <Card padding="lg">
        <EventForm
          // Keyed so a background refresh of the event doesn't wipe half-typed changes
          // but a different event starts clean.
          key={event.id}
          initialValues={toFormValues(event)}
          confirmedCount={event.confirmed_count}
          submitLabel="Save changes"
          isSubmitting={updateEvent.isPending}
          serverError={updateEvent.error && errorMessage(updateEvent.error, "Couldn't save the changes. Try again.")}
          onSubmit={(payload) =>
            updateEvent.mutate(
              { id: event.id, payload },
              {
                onSuccess: () => {
                  showToast("Event updated");
                  navigate(`/events/${event.id}`);
                },
              },
            )
          }
          onCancel={() => navigate(`/events/${event.id}`)}
        />
      </Card>
    </div>
  );
}
