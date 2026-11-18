import { useNavigate } from "react-router-dom";
import { errorMessage } from "../../api/client";
import Card from "../../components/Card";
import { useCreateArticle } from "../../hooks/useArticles";
import { useToast } from "../../hooks/useToast";
import { EMPTY_VALUES } from "./articleFormValues";
import { ArticleForm } from "./ArticleForm";

// Reached only by contributors and admins (WriterRoute in App.tsx).
export function NewArticle() {
  const { showToast } = useToast();
  const navigate = useNavigate();
  const createArticle = useCreateArticle();

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">Write an article</h1>
        <p className="mt-1 text-white/60">Save it as a draft until it's ready, then publish.</p>
      </div>
      <Card padding="lg">
        <ArticleForm
          initialValues={EMPTY_VALUES}
          isEdit={false}
          isSubmitting={createArticle.isPending}
          serverError={createArticle.error && errorMessage(createArticle.error, "Couldn't save the article. Try again.")}
          onSubmit={(payload) =>
            createArticle.mutate(payload, {
              onSuccess: (article) => {
                showToast(article.status === "PUBLISHED" ? "Article published" : "Draft saved");
                navigate(`/articles/${article.slug}`);
              },
            })
          }
          onCancel={() => navigate("/articles")}
        />
      </Card>
    </div>
  );
}
