import Avatar from "../../components/Avatar";
import Badge from "../../components/Badge";
import PrefetchLink from "../../components/PrefetchLink";
import type { ArticleSummary } from "../../types/article";
import { articleDate } from "../../utils/articleLabels";

// One article in the list. The whole card opens it.
export function ArticleCard({ article }: { article: ArticleSummary }) {
  return (
    <article className="relative flex h-full flex-col overflow-hidden rounded-2xl border border-sees-teal/40 bg-gradient-card shadow-sees-card transition-colors hover:border-sees-mint/50">
      {article.cover_image_url && (
        <img
          src={article.cover_image_url}
          alt=""
          width={576}
          height={324}
          loading="lazy"
          decoding="async"
          className="aspect-video w-full object-cover"
        />
      )}
      <div className="flex flex-1 flex-col gap-3 p-4">
        {article.status === "DRAFT" && (
          <div>
            <Badge tone="mustard">Draft</Badge>
          </div>
        )}
        <h3 className="text-lg font-semibold wrap-anywhere text-white">
          <PrefetchLink
            to={`/articles/${article.slug}`}
            className="after:absolute after:inset-0 after:rounded-2xl focus-visible:outline-none focus-visible:after:outline-2 focus-visible:after:outline-sees-mint"
          >
            {article.title}
          </PrefetchLink>
        </h3>
        {article.summary && <p className="line-clamp-3 text-sm wrap-anywhere text-white/70">{article.summary}</p>}
        <div className="mt-auto flex items-center gap-2 pt-2 text-xs text-white/50">
          {article.author && <Avatar name={article.author.full_name} imageUrl={article.author.profile_image_url} />}
          <span className="wrap-anywhere">
            {article.author?.full_name ?? "SEES"} · {articleDate(article)}
          </span>
        </div>
      </div>
    </article>
  );
}
