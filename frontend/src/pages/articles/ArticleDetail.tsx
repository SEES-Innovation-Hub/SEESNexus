import { ArrowLeft, Pencil, Trash } from "lucide-react";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { errorMessage, isNotFoundError } from "../../api/client";
import Avatar from "../../components/Avatar";
import Badge from "../../components/Badge";
import Button from "../../components/Button";
import { buttonClassName } from "../../components/Button/buttonClassName";
import Card from "../../components/Card";
import ConfirmDialog from "../../components/ConfirmDialog";
import ErrorState from "../../components/ErrorState";
import Markdown from "../../components/Markdown";
import PrefetchLink from "../../components/PrefetchLink";
import Skeleton from "../../components/Skeleton";
import { useArticle, useDeleteArticle } from "../../hooks/useArticles";
import { useAuth } from "../../hooks/useAuth";
import { useToast } from "../../hooks/useToast";
import { articleDate, canEditArticle, readingTime } from "../../utils/articleLabels";
import { ArticleNotFound } from "./ArticleNotFound";

export function ArticleDetail() {
  const { slug = "" } = useParams();
  const { user } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const { data: article, error, isPending, isFetching, refetch } = useArticle(slug);
  const deleteArticle = useDeleteArticle();
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  if (isPending) {
    return (
      <div aria-busy="true" aria-label="Loading article" className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-9 w-2/3" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (!article) {
    return isNotFoundError(error) ? <ArticleNotFound /> : <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />;
  }

  const articleId = article.id;

  function handleDelete() {
    deleteArticle.mutate(articleId, {
      onSuccess: () => {
        setConfirmingDelete(false);
        showToast("Article deleted");
        navigate("/articles");
      },
      onError: (deleteError) => {
        setConfirmingDelete(false);
        showToast(errorMessage(deleteError, "Couldn't delete the article. Try again."), "error");
      },
    });
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PrefetchLink to="/articles" className="-my-3 inline-flex items-center gap-1 py-3 text-sm text-sees-mustard hover:text-sees-mint">
        <ArrowLeft aria-hidden="true" className="size-4" />
        All news
      </PrefetchLink>

      <Card as="article" padding="none" className="overflow-hidden">
        {article.cover_image_url && (
          <img src={article.cover_image_url} alt="" width={1152} height={648} className="aspect-video w-full object-cover" />
        )}
        <div className="space-y-6 p-5 sm:p-8">
          <header className="space-y-3">
            {article.status === "DRAFT" && <Badge tone="mustard">Draft · only you and admins can see this</Badge>}
            <h1 className="text-2xl font-semibold wrap-anywhere text-white sm:text-3xl">{article.title}</h1>
            {article.summary && <p className="text-lg wrap-anywhere text-white/70">{article.summary}</p>}
            <div className="flex items-center gap-3 text-sm text-white/50">
              {article.author && <Avatar name={article.author.full_name} imageUrl={article.author.profile_image_url} />}
              <span>
                {article.author?.full_name ?? "SEES"} · {articleDate(article)} · {readingTime(article.content)}
              </span>
            </div>
          </header>

          <Markdown source={article.content} />

          {canEditArticle(article, user) && (
            <div className="flex flex-wrap gap-3 border-t border-sees-teal/40 pt-6">
              <PrefetchLink to={`/articles/${article.slug}/edit`} className={buttonClassName()}>
                <Pencil aria-hidden="true" className="size-4" />
                Edit article
              </PrefetchLink>
              <Button variant="danger" onClick={() => setConfirmingDelete(true)}>
                <Trash aria-hidden="true" className="size-4" />
                Delete
              </Button>
            </div>
          )}
        </div>
      </Card>

      <ConfirmDialog
        open={confirmingDelete}
        title="Delete this article?"
        message={`"${article.title}" will be removed for everyone.`}
        confirmLabel="Delete article"
        onConfirm={handleDelete}
        onCancel={() => setConfirmingDelete(false)}
        isPending={deleteArticle.isPending}
      />
    </div>
  );
}
