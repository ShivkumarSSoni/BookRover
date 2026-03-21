/**
 * Tests for NewBuyerPage — New Buyer sale recording UI behaviours.
 *
 * Mocks useSales hook, SellerContext, NavBar, and react-router-dom navigation.
 * Covers: render with books, quantity controls, buyer form validation,
 * save sale success/error, clear button, redirect if no sellerId.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import NewBuyerPage from '../pages/NewBuyerPage';
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

// ─── useSales mock ────────────────────────────────────────────────────────────

const mockIncrementQty = vi.fn();
const mockDecrementQty = vi.fn();
const mockResetAll = vi.fn();
const mockSubmitSale = vi.fn();

const mockUseSales = vi.fn();
vi.mock('../hooks/useSales', () => ({
  useSales: (...args: unknown[]) => mockUseSales(...args),
}));

// ─── Fixtures ─────────────────────────────────────────────────────────────────

const BOOK_A: BookRover.Book = {
  book_id: 'book-1',
  seller_id: 'seller-123',
  bookstore_id: 'bs-1',
  book_name: 'Thirukkural',
  language: 'Tamil',
  initial_count: 10,
  current_count: 5,
  cost_per_book: 50,
  selling_price: 75,
  current_books_cost_balance: 250,
  total_books_cost_balance: 500,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const BOOK_B: BookRover.Book = {
  book_id: 'book-2',
  seller_id: 'seller-123',
  bookstore_id: 'bs-1',
  book_name: 'Ponniyin Selvan',
  language: 'Tamil',
  initial_count: 8,
  current_count: 3,
  cost_per_book: 120,
  selling_price: 180,
  current_books_cost_balance: 360,
  total_books_cost_balance: 960,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const DEFAULT_SALES_STATE = {
  books: [BOOK_A, BOOK_B],
  isLoadingInventory: false,
  inventoryError: null,
  quantities: {},
  totalBooksSelected: 0,
  totalAmount: 0,
  incrementQty: mockIncrementQty,
  decrementQty: mockDecrementQty,
  resetAll: mockResetAll,
  submitSale: mockSubmitSale,
  isSubmitting: false,
};

function renderPage() {
  return render(
    <MemoryRouter>
      <NewBuyerPage />
    </MemoryRouter>,
  );
}

// ─── Setup ────────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks();
  mockUseSeller.mockReturnValue({ seller: mockSeller, isLoading: false });
  mockUseSales.mockReturnValue(DEFAULT_SALES_STATE);
});

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('NewBuyerPage', () => {
  describe('rendering', () => {
    it('renders the page heading and seller name', () => {
      renderPage();

      expect(screen.getByRole('heading', { name: /new buyer/i })).toBeInTheDocument();
      expect(screen.getByText(/selling as: anand raj/i)).toBeInTheDocument();
    });

    it('renders the NavBar', () => {
      renderPage();

      expect(screen.getByTestId('navbar')).toBeInTheDocument();
    });

    it('renders all available books', () => {
      renderPage();

      expect(screen.getByText('Thirukkural')).toBeInTheDocument();
      expect(screen.getByText('Ponniyin Selvan')).toBeInTheDocument();
    });

    it('renders +/- buttons for each book', () => {
      renderPage();

      expect(screen.getAllByRole('button', { name: /increase quantity/i })).toHaveLength(2);
      expect(screen.getAllByRole('button', { name: /decrease quantity/i })).toHaveLength(2);
    });

    it('renders buyer information section', () => {
      renderPage();

      expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/last name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/phone number/i)).toBeInTheDocument();
    });

    it('pre-fills country code with +91', () => {
      renderPage();

      expect(screen.getByLabelText(/country code/i)).toHaveValue('+91');
    });

    it('shows loading message while inventory loads', () => {
      mockUseSales.mockReturnValue({ ...DEFAULT_SALES_STATE, isLoadingInventory: true });
      renderPage();

      expect(screen.getByText(/loading inventory/i)).toBeInTheDocument();
    });

    it('shows error message on inventory load failure', () => {
      mockUseSales.mockReturnValue({
        ...DEFAULT_SALES_STATE,
        inventoryError: 'Failed to load inventory. Please try again.',
      });
      renderPage();

      expect(screen.getByText(/failed to load inventory/i)).toBeInTheDocument();
    });

    it('shows empty message when no books are available', () => {
      mockUseSales.mockReturnValue({ ...DEFAULT_SALES_STATE, books: [] });
      renderPage();

      expect(screen.getByText(/no books available/i)).toBeInTheDocument();
    });
  });

  describe('navigation guard', () => {
    it('redirects to /register when no seller is in context', () => {
      mockUseSeller.mockReturnValue({ seller: null, isLoading: false });
      renderPage();

      expect(mockNavigate).toHaveBeenCalledWith('/register', { replace: true });
    });
  });

  describe('quantity controls', () => {
    it('calls incrementQty when + button is clicked', async () => {
      const user = userEvent.setup();
      renderPage();

      const increaseButtons = screen.getAllByRole('button', { name: /increase quantity of thirukkural/i });
      await user.click(increaseButtons[0]);

      expect(mockIncrementQty).toHaveBeenCalledWith('book-1');
    });

    it('calls decrementQty when - button is clicked', async () => {
      const user = userEvent.setup();
      // quantity must be > 0 for the decrease button to be enabled
      mockUseSales.mockReturnValue({
        ...DEFAULT_SALES_STATE,
        quantities: { 'book-1': 1 },
        totalBooksSelected: 1,
        totalAmount: 75,
      });
      renderPage();

      const decreaseButtons = screen.getAllByRole('button', { name: /decrease quantity of thirukkural/i });
      await user.click(decreaseButtons[0]);

      expect(mockDecrementQty).toHaveBeenCalledWith('book-1');
    });

    it('shows running total bar when totalBooksSelected > 0', () => {
      mockUseSales.mockReturnValue({
        ...DEFAULT_SALES_STATE,
        quantities: { 'book-1': 2 },
        totalBooksSelected: 2,
        totalAmount: 150,
      });
      renderPage();

      expect(screen.getByText('Books: 2')).toBeInTheDocument();
      expect(screen.getByText('Total: ₹150.00')).toBeInTheDocument();
    });

    it('does not show running total bar when no books are selected', () => {
      renderPage();

      expect(screen.queryByText(/books:/i)).not.toBeInTheDocument();
    });
  });

  describe('Save Sale button', () => {
    it('is disabled when no books are selected', () => {
      renderPage();

      expect(screen.getByRole('button', { name: /save sale/i })).toBeDisabled();
    });

    it('is disabled when buyer fields are empty even if books are selected', () => {
      mockUseSales.mockReturnValue({
        ...DEFAULT_SALES_STATE,
        quantities: { 'book-1': 1 },
        totalBooksSelected: 1,
        totalAmount: 75,
      });
      renderPage();

      expect(screen.getByRole('button', { name: /save sale/i })).toBeDisabled();
    });

    it('is enabled when books are selected and buyer fields are filled', async () => {
      const user = userEvent.setup();
      mockUseSales.mockReturnValue({
        ...DEFAULT_SALES_STATE,
        quantities: { 'book-1': 1 },
        totalBooksSelected: 1,
        totalAmount: 75,
      });
      renderPage();

      await user.type(screen.getByLabelText(/first name/i), 'Ravi');
      await user.type(screen.getByLabelText(/last name/i), 'Kumar');
      await user.type(screen.getByLabelText(/phone number/i), '9876543210');

      expect(screen.getByRole('button', { name: /save sale/i })).not.toBeDisabled();
    });
  });

  describe('sale submission', () => {
    async function fillBuyerAndSubmit(user: ReturnType<typeof userEvent.setup>) {
      await user.type(screen.getByLabelText(/first name/i), 'Ravi');
      await user.type(screen.getByLabelText(/last name/i), 'Kumar');
      await user.type(screen.getByLabelText(/phone number/i), '9876543210');
      await user.click(screen.getByRole('button', { name: /save sale/i }));
    }

    it('shows success banner after successful submission', async () => {
      const user = userEvent.setup();
      mockUseSales.mockReturnValue({
        ...DEFAULT_SALES_STATE,
        quantities: { 'book-1': 2 },
        totalBooksSelected: 2,
        totalAmount: 150,
        submitSale: vi.fn().mockResolvedValue({
          total_books_sold: 2,
          total_amount_collected: 150,
          sale_id: 'sale-1',
        }),
      });
      renderPage();

      await fillBuyerAndSubmit(user);

      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent(/sale saved/i);
      });
    });

    it('shows error banner on submission failure', async () => {
      const user = userEvent.setup();
      mockUseSales.mockReturnValue({
        ...DEFAULT_SALES_STATE,
        quantities: { 'book-1': 2 },
        totalBooksSelected: 2,
        totalAmount: 150,
        submitSale: vi.fn().mockRejectedValue({
          response: { data: { detail: 'Insufficient inventory for book.' } },
        }),
      });
      renderPage();

      await fillBuyerAndSubmit(user);

      await waitFor(() => {
        expect(screen.getByText(/insufficient inventory/i)).toBeInTheDocument();
      });
    });

    it('dismisses error banner when × is clicked', async () => {
      const user = userEvent.setup();
      mockUseSales.mockReturnValue({
        ...DEFAULT_SALES_STATE,
        quantities: { 'book-1': 2 },
        totalBooksSelected: 2,
        totalAmount: 150,
        submitSale: vi.fn().mockRejectedValue({ response: { data: { detail: 'Some error.' } } }),
      });
      renderPage();

      await fillBuyerAndSubmit(user);
      await waitFor(() => expect(screen.getByText('Some error.')).toBeInTheDocument());

      await user.click(screen.getByRole('button', { name: /dismiss error/i }));

      expect(screen.queryByText('Some error.')).not.toBeInTheDocument();
    });
  });

  describe('clear button', () => {
    it('calls resetAll when clear is clicked', async () => {
      const user = userEvent.setup();
      renderPage();

      await user.click(screen.getByRole('button', { name: /clear/i }));

      expect(mockResetAll).toHaveBeenCalled();
    });

    it('clears buyer fields when clear is clicked', async () => {
      const user = userEvent.setup();
      renderPage();

      await user.type(screen.getByLabelText(/first name/i), 'Ravi');
      await user.click(screen.getByRole('button', { name: /clear/i }));

      expect(screen.getByLabelText(/first name/i)).toHaveValue('');
    });
  });
});
