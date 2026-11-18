import type { Article, ArticleSummary } from "../types/article";
import type { User } from "../types/auth";

// Contributors and admins write; everyone signed in reads.
export function canWriteArticles(user: User | null): boolean {
  return user?.role === "CONTRIBUTOR" || user?.role === "ADMIN";
}

// The author or any admin (the backend checks the same).
export function canEditArticle(article: ArticleSummary | Article, user: User | null): boolean {
  return user !== null && (article.author_id === user.id || user.role === "ADMIN");
}

export function articleDate(article: ArticleSummary): string {
  const value = article.published_at ?? article.created_at;
  return new Date(value).toLocaleDateString(undefined, { dateStyle: "long" });
}

// "4 min read", from the word count at a typical 220 words a minute.
export function readingTime(content: string): string {
  const words = content.trim().split(/\s+/).filter(Boolean).length;
  return `${Math.max(1, Math.round(words / 220))} min read`;
}
