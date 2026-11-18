import { useState, type FormEvent } from "react";
import Button from "../../components/Button";
import ImageUploadField from "../../components/ImageUploadField";
import Markdown from "../../components/Markdown";
import Select from "../../components/Select";
import TextArea from "../../components/TextArea";
import TextField from "../../components/TextField";
import type { ArticlePayload, ArticleStatus } from "../../types/article";
import {
  SUMMARY_MAX,
  TITLE_MAX,
  toPayload,
  validate,
  type ArticleFormErrors,
  type ArticleFormValues,
} from "./articleFormValues";

const STATUS_OPTIONS: { value: ArticleStatus; label: string }[] = [
  { value: "DRAFT", label: "Draft (only you and admins can see it)" },
  { value: "PUBLISHED", label: "Published (every member can read it)" },
];

interface ArticleFormProps {
  initialValues: ArticleFormValues;
  isEdit: boolean;
  isSubmitting: boolean;
  serverError: string | null;
  onSubmit: (payload: ArticlePayload) => void;
  onCancel: () => void;
}

export function ArticleForm({ initialValues, isEdit, isSubmitting, serverError, onSubmit, onCancel }: ArticleFormProps) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<ArticleFormErrors>({});
  const [previewing, setPreviewing] = useState(false);

  function update<K extends keyof ArticleFormValues>(field: K, value: ArticleFormValues[K]) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validate(values, isEdit);
    setErrors(found);
    const firstInvalid = Object.keys(found)[0];
    if (firstInvalid) {
      if (firstInvalid === "content") setPreviewing(false);
      // After the preview closes, the textarea is back in the page.
      setTimeout(() => document.getElementById(`article-${firstInvalid}`)?.focus());
      return;
    }
    onSubmit(toPayload(values, isEdit));
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <TextField
        id="article-title"
        label="Title"
        value={values.title}
        onChange={(value) => update("title", value)}
        maxLength={TITLE_MAX}
        error={errors.title}
      />
      <TextArea
        id="article-summary"
        label="Summary"
        rows={2}
        value={values.summary}
        onChange={(value) => update("summary", value)}
        maxLength={SUMMARY_MAX}
        hint="One or two sentences for the article card."
      />

      <div className="space-y-2">
        <div role="group" aria-label="Body view" className="flex gap-2">
          {[
            { key: false, label: "Write" },
            { key: true, label: "Preview" },
          ].map(({ key, label }) => (
            <button
              key={label}
              type="button"
              aria-pressed={previewing === key}
              onClick={() => setPreviewing(key)}
              className={`inline-flex min-h-11 items-center rounded-full border px-4 text-sm font-medium transition-colors ${
                previewing === key
                  ? "border-sees-mint bg-sees-mint/10 text-sees-mint"
                  : "border-sees-teal text-white/70 hover:border-sees-mint/60 hover:text-white"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        {previewing ? (
          <div className="min-h-64 rounded border border-sees-teal bg-sees-void/40 p-4">
            {values.content.trim() ? <Markdown source={values.content} /> : <p className="text-white/40">Nothing to preview yet.</p>}
          </div>
        ) : (
          <TextArea
            id="article-content"
            label="Article"
            required
            rows={16}
            value={values.content}
            onChange={(value) => update("content", value)}
            hint="Markdown: # Heading, **bold**, *italic*, - lists, [link](https://…), ``` code ```."
            error={errors.content}
          />
        )}
      </div>

      <ImageUploadField
        id="article-coverImageUrl"
        label="Cover image"
        value={values.coverImageUrl}
        onChange={(value) => update("coverImageUrl", value)}
        error={errors.coverImageUrl}
      />
      <div className="max-w-md">
        <Select
          id="article-status"
          label="Visibility"
          value={values.status}
          onChange={(value) => value && update("status", value)}
          options={STATUS_OPTIONS}
        />
      </div>
      {isEdit && (
        <TextField
          id="article-slug"
          label="Link name"
          value={values.slug}
          onChange={(value) => update("slug", value)}
          maxLength={255}
          hint="The end of the article's address. Changing it breaks links people already shared."
          error={errors.slug}
        />
      )}

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
          {isEdit ? "Save changes" : values.status === "PUBLISHED" ? "Publish" : "Save draft"}
        </Button>
      </div>
    </form>
  );
}
