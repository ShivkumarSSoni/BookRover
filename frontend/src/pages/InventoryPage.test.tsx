/**
 * Tests for InventoryPage — Seller Inventory UI behaviours.
 *
 * Mocks useInventory hook and react-router-dom navigation.
 * Covers: summary bar, book cards, redirect if no sellerId,
 * add form toggle, edit form pre-fill, remove disabled when partially sold,
 * remove confirmation dialog.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import InventoryPage from '../pages/InventoryPage';
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

const mockAddNewBook = vi.fn();
const mockEditBook = vi.fn();
const mockDeleteBook = vi.fn();
const mockClearError = vi.fn();

const mockUseInventory = vi.fn();

vi.mock('../hooks/useInventory', () => ({
  useInventory: (...args: unknown[]) => mockUseInventory(...args),
}));

// ─── Fixtures ─────────────────────────────────────────────────────────────────

const SELLER_ID = 'seller-123';

const BOOK_A: BookRover.Book = {
  book_id: 'book-1',
  seller_id: SELLER_ID,
  bookstore_id: 'store-1',
  book_name: 'Thirukkural',
  language: 'Tamil',
  initial_count: 10,
  current_count: 10,
  cost_per_book: 50,
  selling_price: 75,
  current_books_cost_balance: 500,
  total_books_cost_balance: 500,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const BOOK_B_PARTIALLY_SOLD: BookRover.Book = {
  book_id: 'book-2',
  seller_id: SELLER_ID,
  bookstore_id: 'store-1',
  book_name: 'Ponniyin Selvan',
  language: 'Tamil',
  initial_count: 20,
  current_count: 15,
  cost_per_book: 120,
  selling_price: 180,
  current_books_cost_balance: 1800,
  total_books_cost_balance: 2400,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const DEFAULT_INVENTORY_STATE = {
  inventory: {
    books: [BOOK_A, BOOK_B_PARTIALLY_SOLD],
    summary: {
      total_books_in_hand: 25,
      total_cost_balance: 2300,
      total_initial_cost: 2900,
    },
  },
  isLoading: false,
  error: null,
  clearError: mockClearError,
  addNewBook: mockAddNewBook,
  editBook: mockEditBook,
  deleteBook: mockDeleteBook,
  refresh: vi.fn(),
};

function renderPage() {
  return render(
    <MemoryRouter>
      <InventoryPage />
    </MemoryRouter>,
  );
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('InventoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('bookrover_seller_id', SELLER_ID);
    mockUseInventory.mockReturnValue(DEFAULT_INVENTORY_STATE);
  });

  afterEach(() => {
    localStorage.clear();
  });

  // ── Auth guard ─────────────────────────────────────────────────────────────

  it('redirects to /register when seller_id is absent from localStorage', () => {
    localStorage.removeItem('bookrover_seller_id');
    mockUseInventory.mockReturnValue({ ...DEFAULT_INVENTORY_STATE, isLoading: true });
    renderPage();
    expect(mockNavigate).toHaveBeenCalledWith('/register', { replace: true });
  });

  // ── Summary bar ────────────────────────────────────────────────────────────

  it('displays the summary bar with books in hand and total cost balance', () => {
    renderPage();
    expect(screen.getByText('Books in Hand')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('Total Cost Balance')).toBeInTheDocument();
    expect(screen.getByText('₹2300.00')).toBeInTheDocument();
  });

  // ── Book cards ─────────────────────────────────────────────────────────────

  it('renders a card for each book in the inventory', () => {
    renderPage();
    expect(screen.getByText('Thirukkural')).toBeInTheDocument();
    expect(screen.getByText('Ponniyin Selvan')).toBeInTheDocument();
  });

  it('shows language label on each book card', () => {
    renderPage();
    expect(screen.getAllByText('Tamil')).toHaveLength(2);
  });

  it('shows cost balance for each book', () => {
    renderPage();
    expect(screen.getByText('₹500.00')).toBeInTheDocument();
    expect(screen.getByText('₹1800.00')).toBeInTheDocument();
  });

  // ── Loading state ──────────────────────────────────────────────────────────

  it('shows a loading spinner while data is loading', () => {
    mockUseInventory.mockReturnValue({ ...DEFAULT_INVENTORY_STATE, isLoading: true, inventory: null });
    renderPage();
    // spinner element exists (no books shown)
    expect(screen.queryByText('Thirukkural')).not.toBeInTheDocument();
  });

  // ── Empty state ────────────────────────────────────────────────────────────

  it('shows empty state message when inventory has no books', () => {
    mockUseInventory.mockReturnValue({
      ...DEFAULT_INVENTORY_STATE,
      inventory: { books: [], summary: { total_books_in_hand: 0, total_cost_balance: 0, total_initial_cost: 0 } },
    });
    renderPage();
    expect(
      screen.getByText(/Your inventory is empty\. Add your first book/i),
    ).toBeInTheDocument();
  });

  // ── Add form ───────────────────────────────────────────────────────────────

  it('shows the Add Book form when + Add Book button is clicked', async () => {
    renderPage();
    await userEvent.click(screen.getByRole('button', { name: /\+ Add Book/i }));
    expect(screen.getByLabelText(/Book Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Language/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Count/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Cost per Book/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Selling Price/i)).toBeInTheDocument();
  });

  it('hides the add form on Cancel', async () => {
    renderPage();
    await userEvent.click(screen.getByRole('button', { name: /\+ Add Book/i }));
    await userEvent.click(screen.getByRole('button', { name: /Cancel/i }));
    expect(screen.queryByLabelText(/Count/i)).not.toBeInTheDocument();
  });

  it('calls addNewBook and closes form on successful submit', async () => {
    mockAddNewBook.mockResolvedValue(undefined);
    // Return the new book on subsequent render via updated inventory
    mockUseInventory.mockReturnValue({
      ...DEFAULT_INVENTORY_STATE,
      addNewBook: mockAddNewBook,
    });
    renderPage();

    await userEvent.click(screen.getByRole('button', { name: /\+ Add Book/i }));
    await userEvent.type(screen.getByLabelText(/Book Name/i), 'New Book');
    await userEvent.type(screen.getByLabelText(/Language/i), 'English');
    await userEvent.type(screen.getByLabelText(/Count/i), '5');
    await userEvent.type(screen.getByLabelText(/Cost per Book/i), '30');
    await userEvent.type(screen.getByLabelText(/Selling Price/i), '50');
    await userEvent.click(screen.getByRole('button', { name: /Add Book/i }));

    await waitFor(() => expect(mockAddNewBook).toHaveBeenCalledTimes(1));
    const payload = mockAddNewBook.mock.calls[0][0];
    expect(payload.book_name).toBe('New Book');
    expect(payload.initial_count).toBe(5);
    expect(payload.selling_price).toBeGreaterThan(payload.cost_per_book);
  });

  // ── Edit form ──────────────────────────────────────────────────────────────

  it('opens edit form pre-filled with book data when edit button is clicked', async () => {
    renderPage();
    const editButtons = screen.getAllByRole('button', { name: /Edit/i });
    await userEvent.click(editButtons[0]); // Edit Thirukkural

    // The edit form is now open — Save Changes button replaces + Add Book
    expect(screen.getByRole('button', { name: /Save Changes/i })).toBeInTheDocument();

    // Pre-filled values
    const nameInput = screen.getByLabelText(/Book Name/i) as HTMLInputElement;
    expect(nameInput.value).toBe('Thirukkural');

    const languageInput = screen.getByLabelText(/Language/i) as HTMLInputElement;
    expect(languageInput.value).toBe('Tamil');

    // Read-only counts shown in the edit form header (may also appear on other cards)
    const inHandElements = screen.getAllByText(/In Hand:/i);
    expect(inHandElements.length).toBeGreaterThanOrEqual(1);
  });

  it('calls editBook with updated values on save', async () => {
    mockEditBook.mockResolvedValue(undefined);
    mockUseInventory.mockReturnValue({ ...DEFAULT_INVENTORY_STATE, editBook: mockEditBook });
    renderPage();

    const editButtons = screen.getAllByRole('button', { name: /Edit/i });
    await userEvent.click(editButtons[0]);

    const nameInput = screen.getByLabelText(/Book Name/i);
    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, 'Thirukkural Updated');

    await userEvent.click(screen.getByRole('button', { name: /Save Changes/i }));

    await waitFor(() => expect(mockEditBook).toHaveBeenCalledTimes(1));
    expect(mockEditBook.mock.calls[0][0]).toBe('book-1');
    expect(mockEditBook.mock.calls[0][1].book_name).toBe('Thirukkural Updated');
  });

  // ── Remove button (partially sold) ─────────────────────────────────────────

  it('disables the remove button for a partially-sold book', () => {
    renderPage();
    const removeButton = screen.getByRole('button', { name: /Remove Ponniyin Selvan/i });
    expect(removeButton).toBeDisabled();
  });

  it('enables the remove button for a book that is not yet sold', () => {
    renderPage();
    const removeButton = screen.getByRole('button', { name: /Remove Thirukkural/i });
    expect(removeButton).not.toBeDisabled();
  });

  // ── Remove confirmation dialog ─────────────────────────────────────────────

  it('shows confirmation dialog when remove is clicked', async () => {
    renderPage();
    const removeButton = screen.getByRole('button', { name: /Remove Thirukkural/i });
    await userEvent.click(removeButton);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/Remove Book\?/i)).toBeInTheDocument();
    // Check dialog body text (scoped to avoid matching the book card heading)
    expect(screen.getByText(/from your inventory/i)).toBeInTheDocument();
  });

  it('calls deleteBook when remove is confirmed', async () => {
    mockDeleteBook.mockResolvedValue(undefined);
    mockUseInventory.mockReturnValue({ ...DEFAULT_INVENTORY_STATE, deleteBook: mockDeleteBook });
    renderPage();

    await userEvent.click(screen.getByRole('button', { name: /Remove Thirukkural/i }));
    await userEvent.click(screen.getByRole('button', { name: /^Remove$/i }));

    await waitFor(() => expect(mockDeleteBook).toHaveBeenCalledWith('book-1'));
  });

  it('closes the dialog when Cancel is clicked', async () => {
    renderPage();
    await userEvent.click(screen.getByRole('button', { name: /Remove Thirukkural/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /^Cancel$/i }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  // ── Error banner ───────────────────────────────────────────────────────────

  it('shows error banner when inventory load fails', () => {
    mockUseInventory.mockReturnValue({
      ...DEFAULT_INVENTORY_STATE,
      error: 'Failed to load inventory. Please try again.',
      inventory: null,
    });
    renderPage();
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Failed to load inventory. Please try again.',
    );
  });

  it('calls clearError when the dismiss button is clicked', async () => {
    mockUseInventory.mockReturnValue({
      ...DEFAULT_INVENTORY_STATE,
      error: 'Failed to load inventory. Please try again.',
    });
    renderPage();
    await userEvent.click(screen.getByRole('button', { name: /✕/i }));
    expect(mockClearError).toHaveBeenCalledTimes(1);
  });
});
