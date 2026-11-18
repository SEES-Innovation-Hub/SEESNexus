import { buttonClassName } from "../../components/Button/buttonClassName";
import EmptyState from "../../components/EmptyState";
import PrefetchLink from "../../components/PrefetchLink";

// A deleted article, someone else's draft, or a mistyped link.
export function ArticleNotFound() {
  return (
    <EmptyState
      title="Article not found"
      message="It may have been removed, or the link is wrong."
      action={
        <PrefetchLink to="/articles" className={buttonClassName("secondary")}>
          Browse news
        </PrefetchLink>
      }
    />
  );
}
