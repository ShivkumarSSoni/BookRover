/**
 * LoginPage — entry point for all BookRover users.
 *
 * Auth mode is controlled by VITE_AUTH_MODE (build-time env var):
 *
 *   mock   — Dev mode. Shows an email form that calls POST /dev/mock-token.
 *            GET /me runs real role-lookup against moto-mocked DynamoDB.
 *            Structurally identical to production — only the token source differs.
 *
 *   cognito — Production mode. Two-step Email OTP flow:
 *             Step 1 — user enters email → Cognito sends a 6-digit OTP to inbox.
 *             Step 2 — user enters the OTP → Cognito validates, issues JWT → GET /me.
 *
 * Redirect logic (both modes — driven by GET /me response):
 *   admin        → /admin
 *   group_leader → /dashboard
 *   seller       → /inventory
 *   (no role)    → /register   (new user, needs to sign up as a seller)
 *
 * If already logged in (valid session on mount), redirects automatically
 * without showing the login form.
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

function isValidOtp(value: string): boolean {
  return /^\d{6}$/.test(value);
}

function roleToPath(roles: BookRover.Role[]): string {
  if (roles.includes('admin')) return '/admin';
  if (roles.includes('group_leader')) return '/dashboard';
  if (roles.includes('seller')) return '/inventory';
  return '/register';
}

export default function LoginPage() {
  const navigate = useNavigate();
  const { me, isLoading, isOtpPending, login, confirmOtp } = useAuth();

  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If already authenticated, redirect immediately.
  useEffect(() => {
    if (!isLoading && me) {
      navigate(roleToPath(me.roles), { replace: true });
    }
  }, [me, isLoading, navigate]);

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValidEmail(email) || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await login(email.trim());
      // mock mode: AuthContext sets `me` → useEffect redirects.
      // cognito mode: AuthContext sets isOtpPending=true → OTP form shown below.
    } catch {
      setError('Could not sign in. Please check the email and try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleOtpSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValidOtp(otp) || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await confirmOtp(otp.trim());
      // AuthContext sets `me` → useEffect redirects.
    } catch {
      setError('Incorrect or expired code. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) return null;
  if (me) return null;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">

        {/* Branding */}
        <div className="mb-10 text-center">
          <h1 className="text-3xl font-brand font-semibold text-blue-600">BookRover</h1>
          <p className="mt-2 text-base text-gray-500">Book Selling Made Simple</p>
        </div>

        {/* ── Step 1: Email form ─────────────────────────────────────────── */}
        {!isOtpPending && (
          <form onSubmit={handleEmailSubmit} noValidate className="space-y-4">
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
              disabled={!isValidEmail(email) || isSubmitting}
              className="w-full min-h-[44px] rounded-lg bg-blue-600 text-white text-base font-semibold py-3 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
            >
              {isSubmitting ? 'Please wait…' : 'Continue'}
            </button>

            {import.meta.env.VITE_AUTH_MODE === 'mock' && (
              <p className="text-center text-xs text-gray-400 pt-2">Dev mode — mock token flow</p>
            )}
          </form>
        )}

        {/* ── Step 2: OTP form (cognito mode only) ──────────────────────── */}
        {isOtpPending && (
          <form onSubmit={handleOtpSubmit} noValidate className="space-y-4">
            <p className="text-sm text-gray-600 text-center">
              We sent a 6-digit code to <strong>{email}</strong>. Enter it below.
            </p>

            <div>
              <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-1">
                Sign-in code
              </label>
              <input
                id="otp"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                placeholder="123456"
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                className="w-full rounded-lg border border-gray-300 px-4 py-3 text-base tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {error && (
              <p role="alert" className="text-sm text-red-600">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={!isValidOtp(otp) || isSubmitting}
              className="w-full min-h-[44px] rounded-lg bg-blue-600 text-white text-base font-semibold py-3 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
            >
              {isSubmitting ? 'Verifying…' : 'Verify code'}
            </button>

            <button
              type="button"
              className="w-full text-sm text-blue-600 underline pt-1"
              onClick={() => {
                setOtp('');
                setError(null);
                // Re-send by returning to email step — user can resubmit the email form.
                window.location.reload();
              }}
            >
              Resend code
            </button>
          </form>
        )}

      </div>
    </div>
  );
}

