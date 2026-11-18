// Mirrors backend/app/schemas/article.py. Keep in sync.
export type ArticleStatus = "DRAFT" | "PUBLISHED";

export interface ArticleAuthor {
  id: string;
  full_name: string;
  profile_image_url: string | null;
}

// A list row: everything except the body.
export interface ArticleSummary {
  id: string;
  title: string;
  slug: string;
  summary: string | null;
  cover_image_url: string | null;
  status: ArticleStatus;
  author_id: string;
  author: ArticleAuthor | null;
  created_at: string;
  updated_at: string;
  // Set the first time it is published, and kept.
  published_at: string | null;
}

export interface Article extends ArticleSummary {
  // Markdown.
  content: string;
}

export interface PaginatedArticles {
  items: ArticleSummary[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ArticlePayload {
  title: string;
  content: string;
  summary: string | null;
  cover_image_url: string | null;
  status: ArticleStatus;
  // Generated from the title when omitted on create; changes only when sent.
  slug?: string;
}
