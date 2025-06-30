/**
 * Standard error payload shape returned by FastAPI per API_CONTRACTS.md.
 * `detail` may be a string (business errors) or an array of validation errors.
 */
export interface APIErrorResponse {
  detail: string | ApiValidationError[];
}

export interface ApiValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

/**
 * Normalized application-level error thrown by the Axios response interceptor.
 */
export class ApiError extends Error {
  public readonly status: number;
  public readonly detail: APIErrorResponse['detail'];

  constructor(status: number, detail: APIErrorResponse['detail']) {
    super(typeof detail === 'string' ? detail : 'Request validation failed');
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}