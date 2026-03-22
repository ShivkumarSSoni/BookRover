/**
 * AuthContext — the single source of truth for the current user's identity.
 *
 * Replaces all scattered localStorage reads across the codebase.
 * On mount, reads the stored token and calls GET /me to restore the session.
 * Exposes login(), logout(), and refreshMe() to the rest of the app.
 *
 * Usage:
 *   - Wrap the entire app in <AuthProvider> inside App.tsx.
 *   - Read identity in any component or context via useAuth().
 */

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { BookRover } from '../types';
import {
  fetchMe,
  mockLogin,
  storeToken,
  clearToken,
  getStoredToken,
} from '../services/authService';

// ─── Context shape ────────────────────────────────────────────────────────────

interface AuthContextValue {
  /** Resolved identity for the current user. Null when not logged in or still loading. */
  me: BookRover.MeResponse | null;
  /** True while the initial session restore is in progress. */
  isLoading: boolean;
  /**
   * Log in with an email address using the dev mock-token endpoint.
   * Stores the token, calls GET /me, and updates state.
   * @throws if the backend call fails (invalid email format, server error).
   */
  login: (email: string) => Promise<void>;
  /** Clear the session — removes the stored token and resets me to null. */
  logout: () => void;
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

  // On mount: if a token is already stored, restore the session via GET /me.
  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    fetchMe()
      .then(setMe)
      .catch(() => {
        // Token is stale or invalid — clear it so the user is sent to /login.
        clearToken();
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (email: string): Promise<void> => {
    const { token } = await mockLogin(email);
    storeToken(token);
    const identity = await fetchMe();
    setMe(identity);
  }, []);

  const logout = useCallback((): void => {
    clearToken();
    setMe(null);
  }, []);

  const refreshMe = useCallback(async (): Promise<void> => {
    const identity = await fetchMe();
    setMe(identity);
  }, []);

  return (
    <AuthContext.Provider value={{ me, isLoading, login, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

/** Returns the current auth context value. Must be used inside <AuthProvider>. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
