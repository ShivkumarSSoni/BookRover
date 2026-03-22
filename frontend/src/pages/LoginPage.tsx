/**
 * LoginPage — entry point for all BookRover users.
 *
 * Development mode flow:
 *   1. User enters any email address.
 *   2. Frontend calls POST /dev/mock-token → stores token.
 *   3. Frontend calls GET /me → resolves roles.
 *   4. Redirects based on role:
 *        admin         → /admin
 *        group_leader  → /dashboard
 *        seller        → /inventory
 *        (none)        → /register (new user, needs to sign up)
 *
 * If already logged in (token in localStorage + valid GET /me), redirects
 * automatically without showing the form.
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

        {/* Login form */}
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
        </form>
      </div>
    </div>
  );
}
