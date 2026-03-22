/**
 * Tests for AdminPage — tab switching behaviour.
 *
 * Mocks the hooks so no real API calls are made during testing.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import AdminPage from '../pages/AdminPage';

const mockLogout = vi.fn();

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ logout: mockLogout }),
}));

// Mock the hooks so no network calls are made
vi.mock('../hooks/useBookstores', () => ({
  useBookstores: () => ({
    bookstores: [],
    isLoading: false,
    error: null,
    clearError: vi.fn(),
    addBookstore: vi.fn(),
    editBookstore: vi.fn(),
    removeBookstore: vi.fn(),
    refresh: vi.fn(),
  }),
}));

vi.mock('../hooks/useGroupLeaders', () => ({
  useGroupLeaders: () => ({
    groupLeaders: [],
    isLoading: false,
    error: null,
    clearError: vi.fn(),
    addGroupLeader: vi.fn(),
    editGroupLeader: vi.fn(),
    removeGroupLeader: vi.fn(),
    refresh: vi.fn(),
  }),
}));

describe('AdminPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page header', () => {
    render(<AdminPage />);
    expect(screen.getByText('BookRover Admin')).toBeInTheDocument();
  });

  it('shows Group Leaders tab by default', () => {
    render(<AdminPage />);
    expect(screen.getByText('+ Add Group Leader')).toBeInTheDocument();
  });

  it('switches to Bookstores tab on click', async () => {
    const user = userEvent.setup();
    render(<AdminPage />);

    await user.click(screen.getByRole('button', { name: /bookstores/i }));

    expect(screen.getByText('+ Add Bookstore')).toBeInTheDocument();
  });

  it('switches back to Group Leaders tab', async () => {
    const user = userEvent.setup();
    render(<AdminPage />);

    await user.click(screen.getByRole('button', { name: /bookstores/i }));
    await user.click(screen.getByRole('button', { name: /group leaders/i }));

    expect(screen.getByText('+ Add Group Leader')).toBeInTheDocument();
  });

  it('calls logout when the Logout button is clicked', async () => {
    const user = userEvent.setup();
    render(<AdminPage />);
    await user.click(screen.getByRole('button', { name: /logout/i }));
    expect(mockLogout).toHaveBeenCalledOnce();
  });
});
