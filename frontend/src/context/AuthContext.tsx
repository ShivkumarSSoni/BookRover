/**
 * AuthContext — the single source of truth for the current user's identity.
 *
 * Supports two auth modes controlled by VITE_AUTH_MODE:
 *
 *   mock   — login(email) calls POST /dev/mock-token, stores the token in
 *            localStorage, then resolves identity via GET /me.
 *
 *   cognito — login(email) initiates the Cognito EMAIL_OTP challenge.
 *             confirmOtp(code) submits the OTP and completes sign-in.
 *             Identity is then resolved via GET /me with the Cognito JWT.
 *
 * Usage:
 *   - Wrap the entire app in <AuthProvider> inside App.tsx.
 *   - Read identity in any component via useAuth().
 */

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';
import { BookRover } from '../types';
import {
  fetchMe,
  mockLogin,
  storeToken,
  clearToken,
  getStoredToken,
  cognitoSignIn,
  cognitoConfirmSignIn,
  cognitoSignOut,
} from '../services/authService';

// ─── Context shape ────────────────────────────────────────────────────────────

interface AuthContextValue {
  /** Resolved identity for the current user. Null when not logged in or still loading. */
  me: BookRover.MeResponse | null;
  /** True while the initial session restore is in progress. */
  isLoading: boolean;
  /**
   * True after login(email) in cognito mode — the OTP code is awaited.
   * LoginPage uses this to switch from the email form to the OTP form.
   */
  isOtpPending: boolean;
  /**
   * Step 1 of auth:
   *   mock mode    — issues a mock token and resolves identity immediately.
   *   cognito mode — initiates the EMAIL_OTP challenge; sets isOtpPending=true.
   * @throws if the backend / Cognito call fails.
   */
  login: (email: string) => Promise<void>;
  /**
   * Step 2 of auth (cognito mode only):
   * Submits the 6-digit OTP received by email. On success, resolves identity
   * via GET /me and clears isOtpPending.
   * @throws if the OTP is wrong or expired.
   */
  confirmOtp: (code: string) => Promise<void>;
  /** Clear the session — removes the stored token / Cognito session and resets me. */
  logout: () => Promise<void>;
  /**
   * Re-fetch GET /me with the current token.
   * Call this after registration so the new seller role is reflected immediately.
   */
  refreshMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ─── Provider ─────────────────────────────────────────────────────────────────

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [me, setMe] = useState<BookRover.MeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isOtpPending, setIsOtpPending] = useState(false);

  // On mount: restore session from stored token (mock) or Amplify session (cognito).
  useEffect(() => {
    async function restoreSession() {
      try {
        if (import.meta.env.VITE_AUTH_MODE === 'cognito') {
          // Amplify stores tokens in its own session; check if one exists.
          const { tokens } = await fetchAuthSession();
          if (tokens?.idToken) {
            const identity = await fetchMe();
            setMe(identity);
          }
        } else {
          const token = getStoredToken();
          if (token) {
            const identity = await fetchMe();
            setMe(identity);
          }
        }
      } catch {
        // Stale or invalid session — clear it so the user is sent to /login.
        if (import.meta.env.VITE_AUTH_MODE !== 'cognito') clearToken();
      } finally {
        setIsLoading(false);
      }
    }
    restoreSession();
  }, []);

  const login = useCallback(async (email: string): Promise<void> => {
    if (import.meta.env.VITE_AUTH_MODE === 'cognito') {
      await cognitoSignIn(email);
      setIsOtpPending(true);
    } else {
      const { token } = await mockLogin(email);
      storeToken(token);
      const identity = await fetchMe();
      setMe(identity);
    }
  }, []);

  const confirmOtp = useCallback(async (code: string): Promise<void> => {
    await cognitoConfirmSignIn(code);
    setIsOtpPending(false);
    const identity = await fetchMe();
    setMe(identity);
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    if (import.meta.env.VITE_AUTH_MODE === 'cognito') {
      await cognitoSignOut();
    } else {
      clearToken();
    }
    setMe(null);
    setIsOtpPending(false);
  }, []);

  const refreshMe = useCallback(async (): Promise<void> => {
    const identity = await fetchMe();
    setMe(identity);
  }, []);

  return (
    <AuthContext.Provider value={{ me, isLoading, isOtpPending, login, confirmOtp, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

