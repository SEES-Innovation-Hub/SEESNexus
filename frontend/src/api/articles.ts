import { api, unwrap } from "./client";
import type { Article, ArticlePayload, ArticleStatus, PaginatedArticles } from "../types/article";

// Every route needs a login (backend/app/api/v1/articles.py). Members see
// published articles; a draft is visible only to its author and admins.

export interface ArticleListParams {
  page?: number;
  pageSize?: number;
  // The caller's own articles, drafts included.
  mine?: boolean;
  status?: ArticleStatus;
  search?: string;
}

// Newest published first.
export function listArticles({ page, pageSize, mine, status, search }: ArticleListParams = {}) {
  return unwrap<PaginatedArticles>(
    api.get("/articles", {
      params: { page, page_size: pageSize, mine: mine || undefined, status, search: search || undefined },
    }),
  );
}

// By id or by slug.
export function getArticle(idOrSlug: string) {
  return unwrap<Article>(api.get(`/articles/${idOrSlug}`));
}

// Contributors and admins.
export function createArticle(payload: ArticlePayload) {
  return unwrap<Article>(api.post("/articles", payload));
}

// The author or an admin.
export function updateArticle(idOrSlug: string, payload: Partial<ArticlePayload>) {
  return unwrap<Article>(api.put(`/articles/${idOrSlug}`, payload));
}

// The author or an admin. Soft delete.
export function deleteArticle(idOrSlug: string) {
  return unwrap<null>(api.delete(`/articles/${idOrSlug}`));
}
