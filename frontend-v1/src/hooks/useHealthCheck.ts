import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/apiClient';

export interface HealthResponse {
  status: string;
  database?: string;
  timestamp?: string;
}

/**
 * Temporary verification hook consumed by the root route to exercise
 * the Axios client + Vite proxy path (`/api/v1/health`). Not a feature hook.
 */
export const useHealthCheck = () => {
  return useQuery<HealthResponse, Error>({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await apiClient.get<HealthResponse>('/health');
      return data;
    },
  });
};