/**
 * Auth API service — HTTP calls for identity resolution and dev login,
 * plus Cognito Email OTP auth (production).
 *
 * Mock mode  (VITE_AUTH_MODE=mock):
 *   mockLogin()  — POST /dev/mock-token — issues a token for any email.
 *   fetchMe()    — GET /me — resolves roles from the stored token.
 *
 * Cognito mode (VITE_AUTH_MODE=cognito):
 *   cognitoSignIn()        — Signs up (new user) or initiates EMAIL_OTP challenge (returning user).
 *   cognitoConfirmSignIn() — Submits the OTP code to complete sign-up or sign-in.
 *   cognitoSignOut()       — Clears the Amplify session.
 *   fetchMe()              — GET /me — resolves roles from the Cognito JWT.
 *
 * New-user flow:
 *   cognitoSignIn() calls signUp() first. Cognito creates the account and
 *   sends a confirmation OTP. cognitoConfirmSignIn() calls confirmSignUp()
 *   then autoSignIn() to issue tokens — no second OTP required.
 *
 * Returning-user flow:
 *   signUp() throws UsernameExistsException → falls through to signIn() with
 *   EMAIL_OTP challenge. cognitoConfirmSignIn() calls confirmSignIn().
 */

import {
  signIn,
  signUp,
  confirmSignIn,
  confirmSignUp,
  autoSignIn,
  signOut,
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

// Tracks which confirmation path the pending OTP belongs to.
// Set by cognitoSignIn(); consumed and cleared by cognitoConfirmSignIn().
type ConfirmPending =
  | { type: 'sign-up'; username: string } // new user — confirmSignUp + autoSignIn
  | { type: 'sign-in' }                   // returning user — confirmSignIn
  | null;

let _confirmPending: ConfirmPending = null;

// Generate a cryptographically random password for signUp.
// The password is never used for authentication — BookRover uses EMAIL_OTP
// exclusively. Cognito's signUp API requires a non-empty password even for
// passwordless pools, so we supply one that satisfies the default policy.
function generatePassword(): string {
  const bytes = new Uint8Array(24);
  crypto.getRandomValues(bytes);
  const hex = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
  return `Bk!${hex}9Z`; // prefix/suffix satisfy uppercase, lowercase, digit, symbol
}

/**
 * Step 1 of Email OTP auth — handles both new and returning users.
 *
 * New user:       calls signUp() → Cognito creates the account and sends an
 *                 OTP confirmation code to the email address.
 * Returning user: signUp() throws UsernameExistsException → falls through to
 *                 signIn() with USER_AUTH / EMAIL_OTP → OTP sent.
 *
 * In both cases the user receives exactly one OTP email and enters it in
 * cognitoConfirmSignIn(). No UI change is needed.
 *
 * @throws for unexpected errors (network failures, invalid config, etc.).
 */
export async function cognitoSignIn(email: string): Promise<void> {
  try {
    await signUp({
      username: email,
      password: generatePassword(),
      options: {
        userAttributes: { email },
        autoSignIn: true,
      },
    });
    // New user — Cognito sent a confirmation OTP.
    _confirmPending = { type: 'sign-up', username: email };
  } catch (err) {
    if ((err as { name?: string }).name === 'UsernameExistsException') {
      // Returning user — initiate EMAIL_OTP sign-in challenge.
      _confirmPending = { type: 'sign-in' };
      await signIn({
        username: email,
        options: { authFlowType: 'USER_AUTH', preferredChallenge: 'EMAIL_OTP' },
      });
      return;
    }
    throw err;
  }
}

/**
 * Step 2 of Email OTP auth — routes to the correct Amplify confirmation call.
 *
 * New user:       confirmSignUp() verifies the account, then autoSignIn()
 *                 exchanges the confirmation session for JWT tokens.
 * Returning user: confirmSignIn() validates the EMAIL_OTP challenge and
 *                 returns JWT tokens directly.
 *
 * After this resolves, Amplify has stored valid tokens in its session store
 * and fetchAuthSession() will return them.
 *
 * @throws if the OTP is wrong, expired, or no sign-in is in progress.
 */
export async function cognitoConfirmSignIn(otp: string): Promise<void> {
  if (_confirmPending?.type === 'sign-up') {
    const { username } = _confirmPending;
    _confirmPending = null;
    await confirmSignUp({ username, confirmationCode: otp });
    await autoSignIn();
  } else {
    _confirmPending = null;
    await confirmSignIn({ challengeResponse: otp });
  }
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

