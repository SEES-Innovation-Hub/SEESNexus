import { useSearchParams } from "react-router-dom";

// List pages keep their filters and page number in the address bar
// (?category=IOT&page=2), so Back/Forward and shared links work and no effect
// is needed to keep state and URL in sync. Used by Projects and Hardware.
export function useUrlFilters() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Math.max(1, Math.floor(Number(searchParams.get("page"))) || 1);
  const isFiltered = [...searchParams.keys()].length > 0;

  // Anything can be typed into the address bar, so a value only counts if the
  // page's guard recognises it; otherwise it means "no filter".
  function read<T extends string>(name: string, isValid: (value: string | null) => value is T) {
    const value = searchParams.get(name);
    return isValid(value) ? value : undefined;
  }

  // Changing a filter starts again from page 1.
  function setFilter(name: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(name, value);
    else next.delete(name);
    next.delete("page");
    setSearchParams(next);
  }

  function setPage(nextPage: number) {
    const next = new URLSearchParams(searchParams);
    if (nextPage > 1) next.set("page", String(nextPage));
    else next.delete("page");
    setSearchParams(next);
    window.scrollTo({ top: 0 });
  }

  return { page, isFiltered, read, setFilter, setPage, clearAll: () => setSearchParams({}) };
}
