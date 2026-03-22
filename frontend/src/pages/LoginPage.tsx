/**
 * LoginPage — entry point for all BookRover users.
 *
 * Auth mode is controlled by VITE_AUTH_MODE (build-time env var):
 *
 *   mock   — Dev mode. Shows an email form that calls POST /dev/mock-token.
 *            GET /me runs real role-lookup against moto-mocked DynamoDB.
 *            Structurally identical to production — only the token source differs.
 *
 *   cognito — Production mode. The mock email form is hidden entirely.
 *             A "Sign in with your organisation account" button is shown instead.
 *             (Cognito Hosted UI integration is configured at deploy time.)
 *
 * Redirect logic (both modes — driven by GET /me response):
 *   admin        → /admin
 *   group_leader → /dashboard
 *   seller       → /inventory
 *   (no role)    → /register   (new user, needs to sign up as a seller)
 *
 * If already logged in (token in localStorage + valid GET /me), redirects
 * automatically without showing the login form.
 *
 * Route: /login
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BookRover } from '../types';

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function roleToPath(roles: BookRover.Role[]): string {
  if (roles.includes('admin')) return '/admin';
  if (roles.includes('group_leader')) return '/dashboard';
  if (roles.includes('seller')) return '/inventory';
  return '/register';
}

export default function LoginPage() {
  const navigate = useNavigate();
  const { me, isLoading, login } = useAuth();

  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If already authenticated, skip the login form and go straight to the correct page.
  useEffect(() => {
    if (!isLoading && me) {
      navigate(roleToPath(me.roles), { replace: true });
    }
  }, [me, isLoading, navigate]);

  const canSubmit = isValidEmail(email) && !isSubmitting;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    setIsSubmitting(true);
    setError(null);

    try {
      await login(email.trim());
      // AuthContext updates `me` after login — the useEffect above will redirect.
    } catch {
      setError('Could not sign in. Please check the email and try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  // Still checking stored token — render nothing to avoid flash.
  if (isLoading) return null;

  // Already authenticated — useEffect will redirect momentarily.
  if (me) return null;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Branding */}
        <div className="mb-10 text-center">
          <h1 className="text-3xl font-brand font-semibold text-blue-600">BookRover</h1>
          <p className="mt-2 text-base text-gray-500">Book Selling Made Simple</p>
        </div>

        {/* Mock login form — only rendered when VITE_AUTH_MODE=mock */}
        {import.meta.env.VITE_AUTH_MODE === 'mock' && (
          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {error && (
              <p role="alert" className="text-sm text-red-600">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={!canSubmit}
              className="w-full min-h-[44px] rounded-lg bg-blue-600 text-white text-base font-semibold py-3 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
            >
              {isSubmitting ? 'Signing in…' : 'Continue'}
            </button>

            <p className="text-center text-xs text-gray-400 pt-2">Dev mode — mock token flow</p>
          </form>
        )}

        {/* Cognito sign-in — only rendered when VITE_AUTH_MODE=cognito */}
        {import.meta.env.VITE_AUTH_MODE === 'cognito' && (
          <div className="space-y-4 text-center">
            <p className="text-base text-gray-600">
              Sign in with your organisation account.
            </p>
            <button
              type="button"
              className="w-full min-h-[44px] rounded-lg bg-blue-600 text-white text-base font-semibold py-3 hover:bg-blue-700 transition-colors"
              onClick={() => {
                // TODO(auth): redirect to Cognito Hosted UI — configure
                // VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_CLIENT_ID at deploy time.
                window.location.href = '/cognito-login';
              }}
            >
              Sign in with Cognito
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
