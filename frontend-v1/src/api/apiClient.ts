import axios, { type AxiosError, type AxiosInstance } from 'axios';
import { ApiError, type APIErrorResponse } from '@/types/api';

/**
 * Centralized Axios HTTP client for the FastAPI backend.
 *
 * Responsibilities per FRONTEND_COMPONENT.md Component #8:
 * - Base URL `/api/v1` (routed through Vite dev proxy or same-origin in production).
 * - Default timeout and JSON headers.
 * - Response interceptor converting `APIErrorResponse` payloads into `ApiError`.
 *
 * UI components MUST NOT import this module directly; they must consume the
 * TanStack Query hooks in `src/hooks/` (per FRONTEND_COMPONENT.md §4 Forbidden Dependencies).
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<APIErrorResponse>) => {
    const status = error.response?.status ?? 0;
    const payload = error.response?.data;

    if (payload && 'detail' in payload) {
      return Promise.reject(new ApiError(status, payload.detail));
    }

    return Promise.reject(
      new ApiError(status, error.message || 'Unexpected network error'),
    );
  },
);