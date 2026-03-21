/**
 * Tests for ReturnPage — Return Books UI behaviours.
 *
 * Mocks: useReturn hook, SellerContext, NavBar, react-router-dom navigation.
 * Covers: loading state, load error, bookstore info, books table, summary cards,
 * empty state (all sold), submit confirmation flow, submit success, submit error,
 * redirect when no sellerId.
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import ReturnPage from '../pages/ReturnPage';
import { BookRover } from '../types';

// ─── Mocks ───────────────────────────────────────────────────────────────────

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../components/NavBar', () => ({
  default: () => <nav data-testid="navbar" />,
}));

const mockSeller: BookRover.Seller = {
  seller_id: 'seller-123',
  first_name: 'Anand',
  last_name: 'Raj',
  email: 'anand@example.com',
  group_leader_id: 'gl-1',
  bookstore_id: 'bs-1',
  status: 'active',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockUseSeller = vi.fn();
vi.mock('../context/SellerContext', () => ({
  useSeller: () => mockUseSeller(),
}));

// ─── useReturn mock ───────────────────────────────────────────────────────────

const mockSubmitReturn = vi.fn();
const mockUseReturn = vi.fn();
vi.mock('../hooks/useReturn', () => ({
  useReturn: (...args: unknown[]) => mockUseReturn(...args),
}));

// ─── Fixture data ─────────────────────────────────────────────────────────────

const mockSummary: BookRover.ReturnSummaryResponse = {
  seller_id: 'seller-123',
  bookstore: {
    bookstore_id: 'bs-1',
    store_name: 'Krishna Books',
    owner_name: 'Sri Krishna',
    address: '12 Temple St, Chennai',
    phone_number: '+919876543210',
  },
  books_to_return: [
    {
      book_id: 'book-1',
      book_name: 'Thirukkural',
      language: 'Tamil',
      quantity_to_return: 8,
      cost_per_book: 50,
      total_cost: 400,
    },
    {
      book_id: 'book-2',
      book_name: 'Ramayanam',
      language: 'Tamil',
      quantity_to_return: 3,
      cost_per_book: 80,
      total_cost: 240,
    },
  ],
  total_books_to_return: 11,
  total_cost_of_unsold_books: 640,
  total_money_collected_from_sales: 225,
};

const defaultUseReturn = {
  summary: mockSummary,
  isLoading: false,
  error: null,
  isSubmitting: false,
  submitSuccess: false,
  submitReturn: mockSubmitReturn,
  submitError: null,
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function renderPage() {
  return render(
    <MemoryRouter>
      <ReturnPage />
    </MemoryRouter>,
  );
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('ReturnPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseSeller.mockReturnValue({ seller: mockSeller });
    mockUseReturn.mockReturnValue({ ...defaultUseReturn });
  });

  it('renders the navbar', () => {
    renderPage();
    expect(screen.getByTestId('navbar')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockUseReturn.mockReturnValue({ ...defaultUseReturn, isLoading: true, summary: null });
    renderPage();
    expect(screen.getByText(/loading return summary/i)).toBeInTheDocument();
  });

  it('shows error state when load fails', () => {
    mockUseReturn.mockReturnValue({
      ...defaultUseReturn,
      isLoading: false,
      summary: null,
      error: 'Failed to load return summary. Please try again.',
    });
    renderPage();
    expect(screen.getByText(/failed to load return summary/i)).toBeInTheDocument();
  });

  it('renders bookstore info card', () => {
    renderPage();
    expect(screen.getByText(/Returning to: Krishna Books/i)).toBeInTheDocument();
    expect(screen.getByText(/Owner: Sri Krishna/i)).toBeInTheDocument();
    expect(screen.getByText(/Address: 12 Temple St, Chennai/i)).toBeInTheDocument();
    expect(screen.getByText(/Phone: \+919876543210/i)).toBeInTheDocument();
  });

  it('renders books in the return table', () => {
    renderPage();
    expect(screen.getByText('Thirukkural')).toBeInTheDocument();
    expect(screen.getByText('Ramayanam')).toBeInTheDocument();
  });

  it('renders summary cards with totals', () => {
    renderPage();
    expect(screen.getByText('11')).toBeInTheDocument(); // unsold books count
    expect(screen.getByText(/₹640\.00/i)).toBeInTheDocument(); // unsold cost
    expect(screen.getByText(/₹225\.00/i)).toBeInTheDocument(); // money to return
  });

  it('shows Submit Return button initially', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /submit return/i })).toBeInTheDocument();
  });

  it('shows confirmation dialog after clicking Submit Return', async () => {
    renderPage();
    await userEvent.click(screen.getByRole('button', { name: /submit return/i }));
    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /confirm return/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('cancels confirmation and shows Submit Return button again', async () => {
    renderPage();
    await userEvent.click(screen.getByRole('button', { name: /submit return/i }));
    await userEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(screen.getByRole('button', { name: /submit return/i })).toBeInTheDocument();
    expect(screen.queryByText(/are you sure/i)).not.toBeInTheDocument();
  });

  it('calls submitReturn when Confirm Return is clicked', async () => {
    renderPage();
    await userEvent.click(screen.getByRole('button', { name: /submit return/i }));
    await userEvent.click(screen.getByRole('button', { name: /confirm return/i }));
    expect(mockSubmitReturn).toHaveBeenCalledOnce();
  });

  it('renders success banner after submit succeeds', () => {
    mockUseReturn.mockReturnValue({ ...defaultUseReturn, submitSuccess: true });
    renderPage();
    expect(screen.getByTestId('success-banner')).toBeInTheDocument();
    expect(screen.getByText(/return submitted successfully/i)).toBeInTheDocument();
  });

  it('renders submit error banner', () => {
    mockUseReturn.mockReturnValue({
      ...defaultUseReturn,
      submitError: 'Failed to submit return. Please try again.',
    });
    renderPage();
    expect(screen.getByTestId('submit-error')).toBeInTheDocument();
    expect(screen.getByText(/failed to submit return/i)).toBeInTheDocument();
  });

  it('renders empty state when no books to return', () => {
    mockUseReturn.mockReturnValue({
      ...defaultUseReturn,
      summary: {
        ...mockSummary,
        books_to_return: [],
        total_books_to_return: 0,
        total_cost_of_unsold_books: 0,
      },
    });
    renderPage();
    const emptyState = screen.getByTestId('empty-state');
    expect(emptyState).toBeInTheDocument();
    expect(screen.getByText(/all books sold/i)).toBeInTheDocument();
    expect(within(emptyState).getByText(/₹225\.00/i)).toBeInTheDocument();
  });

  it('redirects to /register when no sellerId', async () => {
    mockUseSeller.mockReturnValue({ seller: null });
    mockUseReturn.mockReturnValue({ ...defaultUseReturn, summary: null, isLoading: true });
    renderPage();
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/register', { replace: true });
    });
  });

  it('passes sellerId to useReturn hook', () => {
    renderPage();
    expect(mockUseReturn).toHaveBeenCalledWith('seller-123');
  });
});
