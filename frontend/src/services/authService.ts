/**
 * Auth API service — HTTP calls for identity resolution and dev login,
 * plus Cognito Email OTP auth (production).
 *
 * Mock mode  (VITE_AUTH_MODE=mock):
 *   mockLogin()  — POST /dev/mock-token — issues a token for any email.
 *   fetchMe()    — GET /me — resolves roles from the stored token.
 *
 * Cognito mode (VITE_AUTH_MODE=cognito):
 *   cognitoSignIn()        — Initiates EMAIL_OTP challenge via Amplify.
 *   cognitoConfirmSignIn() — Submits the OTP code to complete sign-in.
 *   cognitoSignOut()       — Clears the Amplify session.
 *   cognitoGetIdToken()    — Returns the current Cognito ID token string.
 *   fetchMe()              — GET /me — resolves roles from the Cognito JWT.
 */

import {
  signIn,
  confirmSignIn,
  signOut,
  type SignInOutput,
} from 'aws-amplify/auth';
import apiClient from './apiClient';
import { BookRover } from '../types';

// ─── Mock (dev) auth ──────────────────────────────────────────────────────────

const TOKEN_KEY = 'bookrover_token';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function storeToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export async function mockLogin(email: string): Promise<BookRover.MockTokenResponse> {
  const response = await apiClient.post<BookRover.MockTokenResponse>('/dev/mock-token', { email });
  return response.data;
}

// ─── Cognito (production) auth ────────────────────────────────────────────────

/**
 * Step 1 of Email OTP sign-in.
 * Initiates the USER_AUTH flow requesting an EMAIL_OTP challenge.
 * Cognito sends a 6-digit code to the user's email inbox.
 *
 * @returns The Amplify SignInOutput — check nextStep.signInStep for
 *          'CONFIRM_SIGN_IN_WITH_EMAIL_CODE' to confirm OTP is awaited.
 * @throws if the email is not a registered Cognito user or the call fails.
 */
export async function cognitoSignIn(email: string): Promise<SignInOutput> {
  return signIn({
    username: email,
    options: {
      authFlowType: 'USER_AUTH',
      preferredChallenge: 'EMAIL_OTP',
    },
  });
}

/**
 * Step 2 of Email OTP sign-in.
 * Submits the 6-digit OTP code the user received by email.
 * After success, Amplify stores tokens in its own session store.
 *
 * @throws if the code is wrong, expired, or no sign-in is in progress.
 */
export async function cognitoConfirmSignIn(otp: string): Promise<void> {
  await confirmSignIn({ challengeResponse: otp });
}

/**
 * Signs out of the current Cognito session and clears Amplify's token store.
 */
export async function cognitoSignOut(): Promise<void> {
  await signOut();
}

// ─── Shared ───────────────────────────────────────────────────────────────────

/**
 * Fetch the current user's BookRover identity.
 * The correct Bearer token (mock or Cognito) is attached by apiClient's interceptor.
 *
 * @returns MeResponse with roles, seller_id, and group_leader_id.
 * @throws AxiosError 401 if no valid token is present.
 */
export async function fetchMe(): Promise<BookRover.MeResponse> {
  const response = await apiClient.get<BookRover.MeResponse>('/me');
  return response.data;
}

