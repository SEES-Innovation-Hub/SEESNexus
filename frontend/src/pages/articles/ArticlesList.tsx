import { PenLine } from "lucide-react";
import { useState, type FormEvent } from "react";
import Button from "../../components/Button";
import { buttonClassName } from "../../components/Button/buttonClassName";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import Pagination from "../../components/Pagination";
import PrefetchLink from "../../components/PrefetchLink";
import Skeleton from "../../components/Skeleton";
import TextField from "../../components/TextField";
import { useArticleList } from "../../hooks/useArticles";
import { useAuth } from "../../hooks/useAuth";
import { useUrlFilters } from "../../hooks/useUrlFilters";
import { canWriteArticles } from "../../utils/articleLabels";
import { ArticleCard } from "./ArticleCard";

const PAGE_SIZE = 12;

function isMineFlag(value: string | null): value is "1" {
  return value === "1";
}

function isSearch(value: string | null): value is string {
  return value !== null && value.trim() !== "";
}

export function ArticlesList() {
  const { user } = useAuth();
  const canWrite = canWriteArticles(user);
  const { page, read, setFilter, setPage, clearAll } = useUrlFilters();
  const mine = read("mine", isMineFlag) === "1" && canWrite;
  const search = read("q", isSearch);
  const [draftSearch, setDraftSearch] = useState(search ?? "");

  const { data, isPending, isError, isFetching, isPlaceholderData, refetch } = useArticleList({
    page,
    pageSize: PAGE_SIZE,
    mine,
    search,
  });

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFilter("q", draftSearch.trim());
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-sees-mint">News</h1>
          <p className="mt-1 text-white/60">Stories, write-ups and announcements from SEES.</p>
        </div>
        {canWrite && (
          <PrefetchLink to="/articles/new" className={buttonClassName()}>
            <PenLine aria-hidden="true" className="size-4" />
            Write an article
          </PrefetchLink>
        )}
      </div>

      <div className="flex flex-wrap items-end gap-4">
        <form role="search" onSubmit={handleSearch} className="flex w-full max-w-md items-end gap-2">
          <div className="flex-1">
            <TextField
              id="article-search"
              label="Search titles"
              type="search"
              required={false}
              value={draftSearch}
              onChange={setDraftSearch}
              maxLength={100}
            />
          </div>
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </form>
        {canWrite && (
          <div role="group" aria-label="Show" className="flex gap-2">
            {[
              { key: "", label: "All articles" },
              { key: "1", label: "My articles & drafts" },
            ].map(({ key, label }) => (
              <button
                key={label}
                type="button"
                aria-pressed={(key === "1") === mine}
                onClick={() => setFilter("mine", key)}
                className={`inline-flex min-h-11 items-center rounded-full border px-4 text-sm font-medium transition-colors ${
                  (key === "1") === mine
                    ? "border-sees-mint bg-sees-mint/10 text-sees-mint"
                    : "border-sees-teal text-white/70 hover:border-sees-mint/60 hover:text-white"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        )}
      </div>

      {isPending && (
        <div aria-busy="true" aria-label="Loading articles" className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-56 rounded-2xl" />
          ))}
        </div>
      )}
      {isError && !data && <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />}

      {data && data.items.length === 0 &&
        (search || mine ? (
          <EmptyState
            title="No articles here"
            message={search ? `Nothing has "${search}" in the title.` : "You haven't written anything yet."}
            action={
              <Button
                variant="secondary"
                onClick={() => {
                  setDraftSearch("");
                  clearAll();
                }}
              >
                Show all articles
              </Button>
            }
          />
        ) : (
          <EmptyState
            title="No articles yet"
            message={canWrite ? "Be the first to write one." : "News from SEES will appear here."}
            action={
              canWrite ? (
                <PrefetchLink to="/articles/new" className={buttonClassName()}>
                  Write an article
                </PrefetchLink>
              ) : undefined
            }
          />
        ))}

      {data && data.items.length > 0 && (
        <>
          <ul
            aria-busy={isPlaceholderData}
            className={`grid gap-5 transition-opacity sm:grid-cols-2 xl:grid-cols-3 ${isPlaceholderData ? "opacity-60" : ""}`}
          >
            {data.items.map((article) => (
              <li key={article.id}>
                <ArticleCard article={article} />
              </li>
            ))}
          </ul>
          <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
