import axios, { 
  AxiosError, 
  type AxiosResponse 
} from "axios";
import toast from "react-hot-toast";

import type { ApiErrorResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    if (error.response) {
      const errorData = error.response.data;
      const message = errorData?.message || 'An unexpected server error occurred.';

      toast.error(message, {
        duration: 4000,
        position: 'top-right',
      });
    } else if (error.request) {
      // Network failure / server unreachable
      toast.error('Unable to reach the server. Please check your internet connection.', {
        duration: 5000,
        position: 'top-right',
      });
    } else {
      toast.error(error.message || 'An unknown error occurred.', {
        duration: 4000,
        position: 'top-right',
      });
    }

    return Promise.reject(error);
  }
);