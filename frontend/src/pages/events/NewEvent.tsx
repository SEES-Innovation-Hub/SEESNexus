import { useNavigate } from "react-router-dom";
import { errorMessage } from "../../api/client";
import Card from "../../components/Card";
import { useCreateEvent } from "../../hooks/useEventActions";
import { useToast } from "../../hooks/useToast";
import { EMPTY_VALUES } from "./eventFormValues";
import { EventForm } from "./EventForm";

export function NewEvent() {
  const { showToast } = useToast();
  const navigate = useNavigate();
  const createEvent = useCreateEvent();

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">New event</h1>
        <p className="mt-1 text-white/60">Members can register as soon as you save it.</p>
      </div>
      <Card padding="lg">
        <EventForm
          initialValues={EMPTY_VALUES}
          submitLabel="Create event"
          isSubmitting={createEvent.isPending}
          serverError={createEvent.error && errorMessage(createEvent.error, "Couldn't create the event. Try again.")}
          onSubmit={(payload) =>
            createEvent.mutate(payload, {
              onSuccess: (event) => {
                showToast("Event created");
                navigate(`/events/${event.id}`);
              },
            })
          }
          onCancel={() => navigate("/events")}
        />
      </Card>
    </div>
  );
}
