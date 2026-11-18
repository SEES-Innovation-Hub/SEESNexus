import { useState, type FormEvent } from "react";
import Button from "../../components/Button";
import Checkbox from "../../components/Checkbox";
import ImageUploadField from "../../components/ImageUploadField";
import Select from "../../components/Select";
import TextArea from "../../components/TextArea";
import TextField from "../../components/TextField";
import type { EventPayload } from "../../types/events";
import { EVENT_TYPE_OPTIONS } from "../../utils/eventLabels";
import {
  LOCATION_MAX,
  TITLE_MAX,
  toPayload,
  validate,
  type EventFormErrors,
  type EventFormValues,
} from "./eventFormValues";

interface EventFormProps {
  initialValues: EventFormValues;
  submitLabel: string;
  isSubmitting: boolean;
  serverError: string | null;
  // When editing: people already confirmed, the floor for the place limit.
  confirmedCount?: number;
  onSubmit: (payload: EventPayload) => void;
  onCancel: () => void;
}

// The create and edit forms for an event (admins only). The page around it
// decides what Save does.
export function EventForm({
  initialValues,
  submitLabel,
  isSubmitting,
  serverError,
  confirmedCount = 0,
  onSubmit,
  onCancel,
}: EventFormProps) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<EventFormErrors>({});

  function update<K extends keyof EventFormValues>(field: K, value: EventFormValues[K]) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validate(values, confirmedCount);
    setErrors(found);
    const firstInvalid = Object.keys(found)[0];
    if (firstInvalid) {
      document.getElementById(`event-${firstInvalid}`)?.focus();
      return;
    }
    onSubmit(toPayload(values));
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <TextField
        id="event-title"
        label="Title"
        value={values.title}
        onChange={(value) => update("title", value)}
        maxLength={TITLE_MAX}
        error={errors.title}
      />
      <div className="grid gap-5 sm:grid-cols-2">
        <Select
          id="event-eventType"
          label="Type"
          value={values.eventType}
          onChange={(value) => update("eventType", value)}
          options={EVENT_TYPE_OPTIONS}
          placeholder="Choose a type"
          error={errors.eventType}
        />
        <TextField
          id="event-maxParticipants"
          label="Place limit"
          type="number"
          min="1"
          required={false}
          value={values.maxParticipants}
          onChange={(value) => update("maxParticipants", value)}
          hint="Leave empty for no limit. Extra sign-ups join a waitlist."
          error={errors.maxParticipants}
        />
      </div>
      <TextArea
        id="event-description"
        label="Description"
        required
        rows={6}
        value={values.description}
        onChange={(value) => update("description", value)}
        hint="What happens, who it's for, and what to bring."
        error={errors.description}
      />

      <div className="grid gap-5 sm:grid-cols-3">
        <TextField
          id="event-startDate"
          label="Starts"
          type="datetime-local"
          value={values.startDate}
          onChange={(value) => update("startDate", value)}
          error={errors.startDate}
        />
        <TextField
          id="event-endDate"
          label="Ends"
          type="datetime-local"
          value={values.endDate}
          onChange={(value) => update("endDate", value)}
          error={errors.endDate}
        />
        <TextField
          id="event-registrationDeadline"
          label="Registration closes"
          type="datetime-local"
          value={values.registrationDeadline}
          onChange={(value) => update("registrationDeadline", value)}
          error={errors.registrationDeadline}
        />
      </div>

      <Checkbox
        id="event-isVirtual"
        label="This is an online event"
        checked={values.isVirtual}
        onChange={(checked) => update("isVirtual", checked)}
        hint="The meeting link is only shown to people with a confirmed place."
      />
      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          id="event-location"
          label="Location"
          value={values.location}
          onChange={(value) => update("location", value)}
          maxLength={LOCATION_MAX}
          placeholder={values.isVirtual ? "Online" : "e.g. SEES Innovation Hub, Faculty of Engineering"}
          error={errors.location}
        />
        {values.isVirtual && (
          <TextField
            id="event-virtualLink"
            label="Meeting link"
            type="url"
            value={values.virtualLink}
            onChange={(value) => update("virtualLink", value)}
            placeholder="https://meet.google.com/…"
            error={errors.virtualLink}
          />
        )}
      </div>
      <ImageUploadField
        id="event-bannerUrl"
        label="Banner image"
        value={values.bannerUrl}
        onChange={(value) => update("bannerUrl", value)}
        hint="Shown wide at the top of the event. Landscape works best."
        error={errors.bannerUrl}
      />

      {serverError && (
        <p role="alert" className="text-sm wrap-anywhere text-red-400">
          {serverError}
        </p>
      )}

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <Button variant="secondary" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" isLoading={isSubmitting}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
