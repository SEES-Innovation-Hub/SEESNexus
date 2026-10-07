import { useState, type FormEvent } from "react";
import Button from "../../components/Button";
import Select from "../../components/Select";
import TextArea from "../../components/TextArea";
import TextField from "../../components/TextField";
import type { ProjectPayload } from "../../types/project";
import { CATEGORY_OPTIONS, STATUS_OPTIONS } from "../../utils/projectLabels";
import {
  TITLE_MAX,
  toPayload,
  validate,
  type ProjectFormErrors,
  type ProjectFormValues,
} from "./projectFormValues";
import { TechStackInput } from "./TechStackInput";

interface ProjectFormProps {
  initialValues: ProjectFormValues;
  submitLabel: string;
  isSubmitting: boolean;
  // The server's answer when saving failed (e.g. "You do not have permission…").
  serverError: string | null;
  onSubmit: (payload: ProjectPayload) => void;
  onCancel: () => void;
}

// The create and edit forms. It owns the field values; the page around it
// decides what Save does (create or update) and where to go afterwards.
export function ProjectForm({
  initialValues,
  submitLabel,
  isSubmitting,
  serverError,
  onSubmit,
  onCancel,
}: ProjectFormProps) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<ProjectFormErrors>({});

  // Fixing a field clears its error straight away.
  function update<K extends keyof ProjectFormValues>(field: K, value: ProjectFormValues[K]) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validate(values);
    setErrors(found);
    const firstInvalid = Object.keys(found)[0];
    if (firstInvalid) {
      document.getElementById(`project-${firstInvalid}`)?.focus();
      return;
    }
    onSubmit(toPayload(values));
  }

  return (
    // noValidate: our own messages replace the browser's, so every field reports
    // problems the same way.
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <TextField
        id="project-title"
        label="Title"
        value={values.title}
        onChange={(value) => update("title", value)}
        maxLength={TITLE_MAX}
        error={errors.title}
      />
      <TextArea
        id="project-description"
        label="Description"
        required
        rows={6}
        value={values.description}
        onChange={(value) => update("description", value)}
        hint="What does it do, and what problem does it solve?"
        error={errors.description}
      />
      <div className="grid gap-5 sm:grid-cols-2">
        <Select
          id="project-category"
          label="Category"
          value={values.category}
          onChange={(value) => update("category", value)}
          options={CATEGORY_OPTIONS}
          placeholder="Choose a category"
          error={errors.category}
        />
        <Select
          id="project-status"
          label="Status"
          value={values.status}
          onChange={(value) => value && update("status", value)}
          options={STATUS_OPTIONS}
        />
      </div>
      <TechStackInput value={values.techStack} onChange={(value) => update("techStack", value)} />
      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          id="project-githubUrl"
          label="Source code link"
          type="url"
          required={false}
          value={values.githubUrl}
          onChange={(value) => update("githubUrl", value)}
          placeholder="https://github.com/…"
          error={errors.githubUrl}
        />
        <TextField
          id="project-demoUrl"
          label="Live demo link"
          type="url"
          required={false}
          value={values.demoUrl}
          onChange={(value) => update("demoUrl", value)}
          placeholder="https://…"
          error={errors.demoUrl}
        />
      </div>

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
