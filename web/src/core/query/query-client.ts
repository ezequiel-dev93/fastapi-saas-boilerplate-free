import { QueryClient } from "@tanstack/react-query";
import { HttpError, QuotaExceededError, UnauthorizedError, RateLimitError } from "../api/errors";

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 2, // 2 minutes
        gcTime: 1000 * 60 * 10,   // 10 minutes
        refetchOnWindowFocus: false,
        retry: (failureCount, error) => {
          // Never retry authentication or quota exceeded errors
          if (error instanceof UnauthorizedError || error instanceof QuotaExceededError) {
            return false;
          }

          // Do not retry 4xx errors except 429 RateLimit
          if (error instanceof HttpError) {
            if (error instanceof RateLimitError) {
              return failureCount < 2;
            }
            if (error.status >= 400 && error.status < 500) {
              return false;
            }
          }

          // Retry network or 5xx up to 2 times
          return failureCount < 2;
        },
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
      },
      mutations: {
        retry: false,
      },
    },
  });
}

export const queryClient = createQueryClient();
