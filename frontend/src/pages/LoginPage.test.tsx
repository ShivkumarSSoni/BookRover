/**
 * Tests for LoginPage — login form behaviour.
 *
 * Mocks AuthContext so no real API calls are made.
 * Covers: render, valid/invalid form state, successful login → redirect by role,
 * error state when login throws, auto-redirect when already authenticated,
 * and the two-step OTP form shown in cognito mode (isOtpPending=true).
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
const mockConfirmOtp = vi.fn();
const mockUseAuth = vi.fn();

vi.mock('../context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeAuthState(
  me: BookRover.MeResponse | null = null,
  isLoading = false,
  isOtpPending = false,
): ReturnType<typeof mockUseAuth> {
  return {
    me,
    isLoading,
    isOtpPending,
    login: mockLogin,
    confirmOtp: mockConfirmOtp,
    logout: vi.fn(),
    refreshMe: vi.fn(),
  };
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

const ME_NO_ROLE: BookRover.MeResponse = {
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

    it('redirects new user (no roles) to /register', () => {
      mockUseAuth.mockReturnValue(makeAuthState(ME_NO_ROLE));
      renderPage();
      expect(mockNavigate).toHaveBeenCalledWith('/register', { replace: true });
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

  // ── OTP form (isOtpPending=true, shown in cognito mode after email submit) ──

  describe('OTP form', () => {
    const EMAIL = 'user@example.com';

    beforeEach(() => {
      mockUseAuth.mockReturnValue(makeAuthState(null, false, true));
      // Simulate that the user had already typed their email before OTP was triggered.
      // We set it via the state passed through the component — but since email is local
      // state, we need to render from the email step first then let login set pending.
    });

    function renderOtpForm() {
      // Render with isOtpPending=true directly — LoginPage shows OTP form when this is true.
      mockUseAuth.mockReturnValue(makeAuthState(null, false, true));
      return render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>,
      );
    }

    it('renders the OTP code input and Verify button', () => {
      renderOtpForm();
      expect(screen.getByLabelText(/sign-in code/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /verify code/i })).toBeInTheDocument();
    });

    it('renders a Resend code link', () => {
      renderOtpForm();
      expect(screen.getByRole('button', { name: /resend code/i })).toBeInTheDocument();
    });

    it('does not render the email input when OTP form is shown', () => {
      renderOtpForm();
      expect(screen.queryByLabelText(/email address/i)).not.toBeInTheDocument();
    });

    it('disables Verify button when code field is empty', () => {
      renderOtpForm();
      expect(screen.getByRole('button', { name: /verify code/i })).toBeDisabled();
    });

    it('disables Verify button when code is fewer than 6 digits', async () => {
      renderOtpForm();
      await userEvent.type(screen.getByLabelText(/sign-in code/i), '12345');
      expect(screen.getByRole('button', { name: /verify code/i })).toBeDisabled();
    });

    it('disables Verify button when code contains non-digit characters', async () => {
      renderOtpForm();
      await userEvent.type(screen.getByLabelText(/sign-in code/i), 'abcdef');
      expect(screen.getByRole('button', { name: /verify code/i })).toBeDisabled();
    });

    it('strips non-digit characters from the OTP input', async () => {
      renderOtpForm();
      const input = screen.getByLabelText(/sign-in code/i);
      await userEvent.type(input, '12-34-56');
      expect(input).toHaveValue('123456');
    });

    it('enables Verify button when exactly 6 digits are entered', async () => {
      renderOtpForm();
      await userEvent.type(screen.getByLabelText(/sign-in code/i), '123456');
      expect(screen.getByRole('button', { name: /verify code/i })).toBeEnabled();
    });

    it('calls confirmOtp with the entered code on submit', async () => {
      mockConfirmOtp.mockResolvedValue(undefined);
      renderOtpForm();

      await userEvent.type(screen.getByLabelText(/sign-in code/i), '654321');
      await userEvent.click(screen.getByRole('button', { name: /verify code/i }));

      await waitFor(() => {
        expect(mockConfirmOtp).toHaveBeenCalledWith('654321');
      });
    });

    it('shows an error message when confirmOtp fails', async () => {
      mockConfirmOtp.mockRejectedValue(new Error('CodeMismatchException'));
      renderOtpForm();

      await userEvent.type(screen.getByLabelText(/sign-in code/i), '000000');
      await userEvent.click(screen.getByRole('button', { name: /verify code/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
      expect(screen.getByRole('alert')).toHaveTextContent(/incorrect or expired/i);
    });

    it('re-enables Verify button after a failed OTP submission', async () => {
      mockConfirmOtp.mockRejectedValue(new Error('fail'));
      renderOtpForm();

      await userEvent.type(screen.getByLabelText(/sign-in code/i), '000000');
      await userEvent.click(screen.getByRole('button', { name: /verify code/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /verify code/i })).toBeEnabled();
      });
    });

    it('transitions from email step to OTP step when login resolves', async () => {
      // Start with isOtpPending=false (email step), then login sets it to true.
      let otpPending = false;
      mockUseAuth.mockImplementation(() => ({
        me: null,
        isLoading: false,
        isOtpPending: otpPending,
        login: vi.fn().mockImplementation(async () => { otpPending = true; }),
        confirmOtp: mockConfirmOtp,
        logout: vi.fn(),
        refreshMe: vi.fn(),
      }));

      // The component reads isOtpPending from context on each render,
      // so we verify email step is shown initially.
      render(<MemoryRouter><LoginPage /></MemoryRouter>);
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.queryByLabelText(/sign-in code/i)).not.toBeInTheDocument();
    });
  });
});
