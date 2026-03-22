/**
 * Tests for LoginPage — login form behaviour.
 *
 * Mocks AuthContext so no real API calls are made.
 * Covers: render, valid/invalid form state, successful login → redirect by role,
 * error state when login throws, and auto-redirect when already authenticated.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import LoginPage from './LoginPage';
import { BookRover } from '../types';

// ─── Mocks ───────────────────────────────────────────────────────────────────

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

const mockLogin = vi.fn();
const mockUseAuth = vi.fn();

vi.mock('../context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeAuthState(
  me: BookRover.MeResponse | null = null,
  isLoading = false,
): ReturnType<typeof mockUseAuth> {
  return { me, isLoading, login: mockLogin, logout: vi.fn(), refreshMe: vi.fn() };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  );
}

const ME_SELLER: BookRover.MeResponse = {
  email: 'anand@example.com',
  roles: ['seller'],
  seller_id: 'sel-001',
  group_leader_id: null,
};

const ME_GL: BookRover.MeResponse = {
  email: 'ravi@example.com',
  roles: ['group_leader'],
  seller_id: null,
  group_leader_id: 'gl-001',
};

const ME_ADMIN: BookRover.MeResponse = {
  email: 'admin@example.com',
  roles: ['admin'],
  seller_id: null,
  group_leader_id: null,
};

const ME_NEW_USER: BookRover.MeResponse = {
  email: 'newuser@example.com',
  roles: [],
  seller_id: null,
  group_leader_id: null,
};

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('loading state', () => {
    it('renders nothing while auth is loading', () => {
      mockUseAuth.mockReturnValue(makeAuthState(null, true));
      const { container } = renderPage();
      expect(container).toBeEmptyDOMElement();
    });
  });

  describe('already authenticated', () => {
    it('redirects seller to /inventory without showing form', () => {
      mockUseAuth.mockReturnValue(makeAuthState(ME_SELLER));
      renderPage();
      expect(mockNavigate).toHaveBeenCalledWith('/inventory', { replace: true });
      expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
    });

    it('redirects group_leader to /dashboard', () => {
      mockUseAuth.mockReturnValue(makeAuthState(ME_GL));
      renderPage();
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });

    it('redirects admin to /admin', () => {
      mockUseAuth.mockReturnValue(makeAuthState(ME_ADMIN));
      renderPage();
      expect(mockNavigate).toHaveBeenCalledWith('/admin', { replace: true });
    });
  });

  describe('login form render', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue(makeAuthState());
    });

    it('renders the BookRover branding', () => {
      renderPage();
      expect(screen.getByText('BookRover')).toBeInTheDocument();
      expect(screen.getByText('Book Selling Made Simple')).toBeInTheDocument();
    });

    it('renders the email field and Continue button', () => {
      renderPage();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /continue/i })).toBeInTheDocument();
    });

    it('disables Continue button when email is empty', () => {
      renderPage();
      expect(screen.getByRole('button', { name: /continue/i })).toBeDisabled();
    });

    it('disables Continue button when email is invalid', async () => {
      renderPage();
      await userEvent.type(screen.getByLabelText(/email address/i), 'not-an-email');
      expect(screen.getByRole('button', { name: /continue/i })).toBeDisabled();
    });

    it('enables Continue button when a valid email is entered', async () => {
      renderPage();
      await userEvent.type(screen.getByLabelText(/email address/i), 'test@example.com');
      expect(screen.getByRole('button', { name: /continue/i })).toBeEnabled();
    });
  });

  describe('successful login', () => {
    it('calls login with the entered email on submit', async () => {
      mockUseAuth.mockReturnValue(makeAuthState());
      mockLogin.mockResolvedValue(undefined);
      renderPage();

      await userEvent.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await userEvent.click(screen.getByRole('button', { name: /continue/i }));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith('test@example.com');
      });
    });

    it('trims whitespace from the email before calling login', async () => {
      mockUseAuth.mockReturnValue(makeAuthState());
      mockLogin.mockResolvedValue(undefined);
      renderPage();

      await userEvent.type(screen.getByLabelText(/email address/i), '  test@example.com  ');
      await userEvent.click(screen.getByRole('button', { name: /continue/i }));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith('test@example.com');
      });
    });
  });

  describe('login error', () => {
    it('shows an error message when login fails', async () => {
      mockUseAuth.mockReturnValue(makeAuthState());
      mockLogin.mockRejectedValue(new Error('Network error'));
      renderPage();

      await userEvent.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await userEvent.click(screen.getByRole('button', { name: /continue/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
      expect(screen.getByRole('alert')).toHaveTextContent(/could not sign in/i);
    });

    it('re-enables the Continue button after a failed login', async () => {
      mockUseAuth.mockReturnValue(makeAuthState());
      mockLogin.mockRejectedValue(new Error('fail'));
      renderPage();

      await userEvent.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await userEvent.click(screen.getByRole('button', { name: /continue/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue/i })).toBeEnabled();
      });
    });
  });
});
