import { useNavigate, useParams } from "react-router-dom";
import { errorMessage, isNotFoundError } from "../../api/client";
import Card from "../../components/Card";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import Skeleton from "../../components/Skeleton";
import { useArticle, useUpdateArticle } from "../../hooks/useArticles";
import { useAuth } from "../../hooks/useAuth";
import { useToast } from "../../hooks/useToast";
import { canEditArticle } from "../../utils/articleLabels";
import { toFormValues } from "./articleFormValues";
import { ArticleForm } from "./ArticleForm";
import { ArticleNotFound } from "./ArticleNotFound";

export function EditArticle() {
  const { slug = "" } = useParams();
  const { user } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const { data: article, error, isPending, isFetching, refetch } = useArticle(slug);
  const updateArticle = useUpdateArticle();

  if (isPending) {
    return (
      <div aria-busy="true" aria-label="Loading article" className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-9 w-48" />
        <Skeleton className="h-96 rounded-2xl" />
      </div>
    );
  }
  if (!article) {
    return isNotFoundError(error) ? <ArticleNotFound /> : <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />;
  }
  if (!canEditArticle(article, user)) {
    return <EmptyState title="You can't edit this article" message="Only its author and admins can change it." />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">Edit article</h1>
        <p className="mt-1 wrap-anywhere text-white/60">{article.title}</p>
      </div>
      <Card padding="lg">
        <ArticleForm
          key={article.id}
          initialValues={toFormValues(article)}
          isEdit
          isSubmitting={updateArticle.isPending}
          serverError={updateArticle.error && errorMessage(updateArticle.error, "Couldn't save the changes. Try again.")}
          onSubmit={(payload) =>
            updateArticle.mutate(
              { id: article.id, payload },
              {
                onSuccess: (saved) => {
                  showToast("Article updated");
                  navigate(`/articles/${saved.slug}`, { replace: true });
                },
              },
            )
          }
          onCancel={() => navigate(`/articles/${article.slug}`)}
        />
      </Card>
    </div>
  );
}
