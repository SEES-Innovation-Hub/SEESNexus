import type { Article, ArticlePayload, ArticleStatus } from "../../types/article";
import { isHttpUrl } from "../../utils/isHttpUrl";

export interface ArticleFormValues {
  title: string;
  summary: string;
  content: string;
  coverImageUrl: string;
  status: ArticleStatus;
  // Edit only: the article's link name. "" on create means "make one from the title".
  slug: string;
}

export type ArticleFormErrors = Partial<Record<keyof ArticleFormValues, string>>;

// Limits match backend/app/schemas/article.py.
export const TITLE_MAX = 255;
export const SUMMARY_MAX = 500;
export const URL_MAX = 500;
const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export const EMPTY_VALUES: ArticleFormValues = {
  title: "",
  summary: "",
  content: "",
  coverImageUrl: "",
  status: "DRAFT",
  slug: "",
};

export function toFormValues(article: Article): ArticleFormValues {
  return {
    title: article.title,
    summary: article.summary ?? "",
    content: article.content,
    coverImageUrl: article.cover_image_url ?? "",
    status: article.status,
    slug: article.slug,
  };
}

export function validate(values: ArticleFormValues, isEdit: boolean): ArticleFormErrors {
  const cover = values.coverImageUrl.trim();
  const slug = values.slug.trim();
  const errors: ArticleFormErrors = {
    title: values.title.trim() ? undefined : "Give the article a title.",
    content: values.content.trim() ? undefined : "Write something before saving.",
    coverImageUrl:
      cover === ""
        ? undefined
        : !isHttpUrl(cover)
          ? "Enter a full link starting with https://"
          : cover.length > URL_MAX
            ? `Keep the link under ${URL_MAX} characters.`
            : undefined,
    slug:
      isEdit && !SLUG_PATTERN.test(slug)
        ? "Use lowercase letters, numbers and single hyphens, e.g. floodguard-wins-award."
        : undefined,
  };
  return Object.fromEntries(Object.entries(errors).filter(([, message]) => message)) as ArticleFormErrors;
}

export function toPayload(values: ArticleFormValues, isEdit: boolean): ArticlePayload {
  return {
    title: values.title.trim(),
    summary: values.summary.trim() || null,
    content: values.content.trim(),
    cover_image_url: values.coverImageUrl.trim() || null,
    status: values.status,
    ...(isEdit ? { slug: values.slug.trim() } : {}),
  };
}
