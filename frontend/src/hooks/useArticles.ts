import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createArticle,
  deleteArticle,
  getArticle,
  listArticles,
  updateArticle,
  type ArticleListParams,
} from "../api/articles";
import { queryKeys } from "../api/queryKeys";
import type { ArticlePayload } from "../types/article";

// Reads and changes for the Articles pages, kept together like useEvents /
// useEventActions.

export function useArticleList(params: ArticleListParams) {
  return useQuery({
    queryKey: queryKeys.articles.list(params),
    queryFn: () => listArticles(params),
    placeholderData: keepPreviousData,
  });
}

export function useArticle(idOrSlug: string) {
  return useQuery({ queryKey: queryKeys.articles.detail(idOrSlug), queryFn: () => getArticle(idOrSlug) });
}

// Articles are opened by slug, so after a change the slug's cache entry is
// filled straight away and the lists are refreshed.
export function useCreateArticle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createArticle,
    onSuccess: (article) => {
      queryClient.setQueryData(queryKeys.articles.detail(article.slug), article);
      void queryClient.invalidateQueries({ queryKey: queryKeys.articles.lists });
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
    },
  });
}

export function useUpdateArticle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<ArticlePayload> }) => updateArticle(id, payload),
    onSuccess: (article) => {
      // Drop every cached copy (it may be cached under an old slug), then seed the new one.
      queryClient.removeQueries({ queryKey: ["articles", "detail"] });
      queryClient.setQueryData(queryKeys.articles.detail(article.slug), article);
      void queryClient.invalidateQueries({ queryKey: queryKeys.articles.lists });
    },
  });
}

export function useDeleteArticle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteArticle,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.articles.all });
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.stats });
    },
  });
}
