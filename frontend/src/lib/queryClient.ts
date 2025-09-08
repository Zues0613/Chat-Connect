import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache data for 5 minutes
      staleTime: 5 * 60 * 1000,
      // Keep data in cache for 10 minutes
      gcTime: 10 * 60 * 1000,
      // Retry failed requests 2 times
      retry: 2,
      // Refetch on window focus (good for real-time updates)
      refetchOnWindowFocus: true,
      // Refetch on reconnect
      refetchOnReconnect: true,
      // Don't refetch on mount if data is fresh
      refetchOnMount: false,
    },
    mutations: {
      // Retry failed mutations 1 time
      retry: 1,
      // Optimistic updates for better UX
      onMutate: true,
    },
  },
});

// Prefetch common data
export const prefetchCommonData = async () => {
  // Prefetch user profile, settings, etc.
  await queryClient.prefetchQuery({
    queryKey: ['user-profile'],
    queryFn: () => fetch('/api/user/profile').then(res => res.json()),
  });
};
