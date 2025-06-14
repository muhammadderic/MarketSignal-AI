/**
 * Time duration conversion utilities returning milliseconds.
 */
export const seconds = (s: number): number => s * 1000;
export const minutes = (m: number): number => m * 60 * 1000;
export const hours = (h: number): number => h * 60 * 60 * 1000;