export interface ApiErrorResponse {
  status: number;
  code: string;
  message: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  details?: Record<string, any> | null;
}