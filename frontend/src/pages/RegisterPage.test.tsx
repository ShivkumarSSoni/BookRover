/**
 * Tests for RegisterPage — registration form behaviour.
 *
 * Mocks the hook and service so no real API calls are made.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import RegisterPage from './RegisterPage';

// Mock the hook that fetches group leaders
vi.mock('../hooks/useGroupLeaderLookup', () => ({
  useGroupLeaderLookup: vi.fn(),
}));

// Mock the seller service
vi.mock('../services/sellerService', () => ({
  registerSeller: vi.fn(),
}));

// Mock AuthContext
const mockRefreshMe = vi.fn();
// currentMe is module-level so mockRefreshMe implementations can update it;
// the component re-renders (triggered by setIsSubmitting(false) in finally)
// will pick up the new value when useAuth() is called again.
let currentMe: { email: string; roles: string[]; seller_id?: string } | null = null;
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ me: currentMe, isLoading: false, login: vi.fn(), logout: vi.fn(), refreshMe: mockRefreshMe }),
}));

// Mock react-router-dom navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

import { useGroupLeaderLookup } from '../hooks/useGroupLeaderLookup';
import { registerSeller } from '../services/sellerService';

const mockUseGroupLeaderLookup = useGroupLeaderLookup as ReturnType<typeof vi.fn>;
const mockRegisterSeller = registerSeller as ReturnType<typeof vi.fn>;

const DROPDOWN_OPTIONS = [
  {
    label: 'Ravi Kumar \u2014 Sri Lakshmi Books',
    group_leader_id: 'gl-001',
    bookstore_id: 'bs-001',
  },
];

function renderPage() {
  return render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>,
  );
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default: authenticated user with no role yet — the valid state for /register.
    currentMe = { email: 'priya@gmail.com', roles: [] };
    mockUseGroupLeaderLookup.mockReturnValue({
      options: DROPDOWN_OPTIONS,
      isLoading: false,
      error: null,
    });
  });

  // ── Auth guard ────────────────────────────────────────────────────────────────

  it('redirects to /login when no authenticated user is present', () => {
    currentMe = null;
    renderPage();
    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
  });

  // ── Render ──────────────────────────────────────────────────────────────────

  it('renders the page heading and form fields', () => {
    renderPage();

    expect(screen.getByText('Seller Registration')).toBeInTheDocument();
    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/last name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/group leader/i)).toBeInTheDocument();
  });

  it('renders the Register button disabled initially', () => {
    renderPage();

    expect(screen.getByRole('button', { name: /register/i })).toBeDisabled();
  });

  // ── Loading state ────────────────────────────────────────────────────────────

  it('shows loading indicator while fetching groups', () => {
    mockUseGroupLeaderLookup.mockReturnValue({
      options: [],
      isLoading: true,
      error: null,
    });

    renderPage();

    expect(screen.getByText(/loading groups/i)).toBeInTheDocument();
  });

  // ── Empty state ──────────────────────────────────────────────────────────────

  it('shows empty state message when no groups are configured', () => {
    mockUseGroupLeaderLookup.mockReturnValue({
      options: [],
      isLoading: false,
      error: null,
    });

    renderPage();

    expect(screen.getByText(/no groups are set up yet/i)).toBeInTheDocument();
  });

  // ── Lookup error ─────────────────────────────────────────────────────────────

  it('shows error alert when group leader lookup fails', () => {
    mockUseGroupLeaderLookup.mockReturnValue({
      options: [],
      isLoading: false,
      error: 'Failed to load group leaders. Please try again.',
    });

    renderPage();

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Failed to load group leaders. Please try again.',
    );
  });

  // ── Validation ───────────────────────────────────────────────────────────────

  it('enables Register button when all fields are valid', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText(/first name/i), 'Priya');
    await user.type(screen.getByLabelText(/last name/i), 'Sharma');
    await user.type(screen.getByLabelText(/email/i), 'priya@gmail.com');
    await user.selectOptions(
      screen.getByLabelText(/group leader/i),
      screen.getByRole('option', { name: /ravi kumar/i }),
    );

    expect(screen.getByRole('button', { name: /register/i })).toBeEnabled();
  });

  // ── Happy path ───────────────────────────────────────────────────────────────

  it('calls registerSeller with correct payload and navigates to /inventory after role update', async () => {
    const user = userEvent.setup();
    mockRegisterSeller.mockResolvedValue({ seller_id: 'sel-001' });
    // Simulate AuthContext committing the seller role after refreshMe resolves.
    // The component re-renders (via setIsSubmitting(false)) and useAuth() picks
    // up the new currentMe, which triggers the navigation useEffect.
    mockRefreshMe.mockImplementation(async () => {
      currentMe = { email: 'priya@gmail.com', roles: ['seller'], seller_id: 'sel-001' };
    });
    renderPage();

    await user.type(screen.getByLabelText(/first name/i), 'Priya');
    await user.type(screen.getByLabelText(/last name/i), 'Sharma');
    await user.type(screen.getByLabelText(/email/i), 'priya@gmail.com');
    await user.selectOptions(
      screen.getByLabelText(/group leader/i),
      screen.getByRole('option', { name: /ravi kumar/i }),
    );

    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(mockRegisterSeller).toHaveBeenCalledWith({
        first_name: 'Priya',
        last_name: 'Sharma',
        email: 'priya@gmail.com',
        group_leader_id: 'gl-001',
        bookstore_id: 'bs-001',
      });
      expect(mockRefreshMe).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/inventory', { replace: true });
    });
  });

  // ── Error state ───────────────────────────────────────────────────────────────

  it('shows server error message on failed registration', async () => {
    const user = userEvent.setup();
    mockRegisterSeller.mockRejectedValue({
      response: { data: { detail: "Email 'priya@gmail.com' is already registered." } },
    });
    renderPage();

    await user.type(screen.getByLabelText(/first name/i), 'Priya');
    await user.type(screen.getByLabelText(/last name/i), 'Sharma');
    await user.type(screen.getByLabelText(/email/i), 'priya@gmail.com');
    await user.selectOptions(
      screen.getByLabelText(/group leader/i),
      screen.getByRole('option', { name: /ravi kumar/i }),
    );

    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('already registered');
    });
  });

  it('shows generic error when server returns no detail', async () => {
    const user = userEvent.setup();
    mockRegisterSeller.mockRejectedValue(new Error('Network Error'));
    renderPage();

    await user.type(screen.getByLabelText(/first name/i), 'Priya');
    await user.type(screen.getByLabelText(/last name/i), 'Sharma');
    await user.type(screen.getByLabelText(/email/i), 'priya@gmail.com');
    await user.selectOptions(
      screen.getByLabelText(/group leader/i),
      screen.getByRole('option', { name: /ravi kumar/i }),
    );

    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Registration failed');
    });
  });
});
