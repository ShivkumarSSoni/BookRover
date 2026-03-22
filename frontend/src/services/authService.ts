/**
 * Auth API service — HTTP calls for identity resolution and dev login.
 *
 * fetchMe()     — GET /me — decodes the stored token and returns the caller's roles + IDs.
 * mockLogin()   — POST /dev/mock-token — (dev only) issues a token for any email.
 *
 * The stored token is automatically attached to all requests by the axios
 * request interceptor configured in apiClient.ts.
 */

import apiClient from './apiClient';
import { BookRover } from '../types';

const TOKEN_KEY = 'bookrover_token';

/** Retrieve the stored dev token, or null if not present. */
export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/** Persist the token to localStorage. */
export function storeToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/** Remove the stored token (logout). */
export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Fetch the current user's BookRover identity.
 * Requires a Bearer token to be present in localStorage (set by storeToken).
 *
 * @returns MeResponse with roles, seller_id, and group_leader_id.
 * @throws AxiosError 401 if no valid token is present.
 */
export async function fetchMe(): Promise<BookRover.MeResponse> {
  const response = await apiClient.get<BookRover.MeResponse>('/me');
  return response.data;
}

/**
 * Issue a dev-only mock token for the given email address.
 * Calls POST /dev/mock-token — only available when APP_ENV != prod.
 *
 * @param email - Any email address to issue a token for.
 * @returns MockTokenResponse with the token string and the email it represents.
 * @throws AxiosError 422 for invalid email format.
 */
export async function mockLogin(email: string): Promise<BookRover.MockTokenResponse> {
  const response = await apiClient.post<BookRover.MockTokenResponse>('/dev/mock-token', { email });
  return response.data;
}
