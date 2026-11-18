import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { queryKeys } from "../api/queryKeys";
import { searchUsers } from "../api/users";

export const MIN_SEARCH_LENGTH = 2;

// Members matching a name, for the teammate picker. Nothing is asked for until
// two characters are typed; the previous results stay while the next load.
export function useUserSearch(query: string) {
  const q = query.trim();
  return useQuery({
    queryKey: queryKeys.users.search(q),
    queryFn: () => searchUsers(q),
    enabled: q.length >= MIN_SEARCH_LENGTH,
    placeholderData: keepPreviousData,
    staleTime: 60_000,
  });
}
