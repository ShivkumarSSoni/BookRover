/**
 * Tests for BookstoresTab — render, add, edit, delete interactions.
 *
 * BookstoresTab receives state and mutation functions as props (lifted to AdminPage).
 * Tests pass props directly — no hook mocking needed.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import BookstoresTab from '../pages/BookstoresTab';
import { BookRover } from '../types';

const MOCK_BOOKSTORE: BookRover.BookStore = {
  bookstore_id: 'bs-001',
  store_name: 'Sri Lakshmi Books',
  owner_name: 'Lakshmi Devi',
  address: '12 MG Road, Chennai',
  phone_number: '+914423456789',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const mockAddBookstore = vi.fn();
const mockEditBookstore = vi.fn();
const mockRemoveBookstore = vi.fn();
const mockClearError = vi.fn();

const DEFAULT_PROPS = {
  bookstores: [MOCK_BOOKSTORE],
  isLoading: false,
  error: null,
  clearError: mockClearError,
  addBookstore: mockAddBookstore,
  editBookstore: mockEditBookstore,
  removeBookstore: mockRemoveBookstore,
};

describe('BookstoresTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the bookstore card with all fields', () => {
    render(<BookstoresTab {...DEFAULT_PROPS} />);
    expect(screen.getByText('Sri Lakshmi Books')).toBeInTheDocument();
    expect(screen.getByText(/Lakshmi Devi/i)).toBeInTheDocument();
    expect(screen.getByText(/12 MG Road/i)).toBeInTheDocument();
  });

  it('shows add form when "+ Add Bookstore" is clicked', async () => {
    const user = userEvent.setup();
    render(<BookstoresTab {...DEFAULT_PROPS} />);

    await user.click(screen.getByText('+ Add Bookstore'));

    expect(screen.getByPlaceholderText('Sri Lakshmi Books')).toBeInTheDocument();
  });

  it('Save button is disabled when form is empty', async () => {
    const user = userEvent.setup();
    render(<BookstoresTab {...DEFAULT_PROPS} />);

    await user.click(screen.getByText('+ Add Bookstore'));

    const saveButton = screen.getByRole('button', { name: /^save$/i });
    expect(saveButton).toBeDisabled();
  });

  it('calls addBookstore with form data on Save', async () => {
    const user = userEvent.setup();
    mockAddBookstore.mockResolvedValue(undefined);
    render(<BookstoresTab {...DEFAULT_PROPS} />);

    await user.click(screen.getByText('+ Add Bookstore'));
    await user.type(screen.getByPlaceholderText('Sri Lakshmi Books'), 'Test Store');
    await user.type(screen.getByPlaceholderText('Lakshmi Devi'), 'Test Owner');
    await user.type(screen.getByPlaceholderText(/12 MG Road/i), 'Test Address');
    await user.type(screen.getByPlaceholderText('+914423456789'), '+914423456789');

    await user.click(screen.getByRole('button', { name: /^save$/i }));

    await waitFor(() => {
      expect(mockAddBookstore).toHaveBeenCalledWith({
        store_name: 'Test Store',
        owner_name: 'Test Owner',
        address: 'Test Address',
        phone_number: '+914423456789',
      });
    });
  });

  it('shows edit form when Edit is clicked', async () => {
    const user = userEvent.setup();
    render(<BookstoresTab {...DEFAULT_PROPS} />);

    await user.click(screen.getByRole('button', { name: /edit/i }));

    expect(screen.getByText('Edit Bookstore')).toBeInTheDocument();
  });

  it('shows confirm dialog when Delete is clicked', async () => {
    const user = userEvent.setup();
    render(<BookstoresTab {...DEFAULT_PROPS} />);

    await user.click(screen.getByRole('button', { name: /delete/i }));

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/cannot be undone/i)).toBeInTheDocument();
  });

  it('calls removeBookstore when deletion is confirmed', async () => {
    const user = userEvent.setup();
    mockRemoveBookstore.mockResolvedValue(undefined);
    render(<BookstoresTab {...DEFAULT_PROPS} />);

    await user.click(screen.getByRole('button', { name: /delete/i }));
    await user.click(screen.getByRole('button', { name: /confirm/i }));

    await waitFor(() => {
      expect(mockRemoveBookstore).toHaveBeenCalledWith('bs-001');
    });
  });

  it('dismisses confirm dialog on Cancel', async () => {
    const user = userEvent.setup();
    render(<BookstoresTab {...DEFAULT_PROPS} />);

    await user.click(screen.getByRole('button', { name: /delete/i }));
    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
