import { QueryClient } from "@tanstack/react-query";
import axios from "axios";

// One shared cache for every API read in the app. Screens ask for data through
// useQuery (see hooks/), so two screens showing the same list share one request,
// and going back to a page shows its data instantly while it refreshes quietly.
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Data younger than 30s is shown without asking the server again.
      staleTime: 30_000,
      // Retry once on network trouble or a server error; a 4xx (not found,
      // forbidden, bad input) will give the same answer again, so don't.
      retry: (failureCount, error) => {
        const status = axios.isAxiosError(error) ? error.response?.status : undefined;
        if (status !== undefined && status >= 400 && status < 500) return false;
        return failureCount < 1;
      },
    },
  },
});
