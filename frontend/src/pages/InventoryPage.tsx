/**
 * InventoryPage — Seller Inventory management page.
 *
 * Allows a seller to view, add, edit, and remove books from their inventory.
 * Displays a sticky summary bar (books in hand, total cost balance) and a
 * card list of all books with inline add/edit forms.
 *
 * seller_id is read from localStorage (set during registration).
 * If absent, redirects to /register.
 *
 * Route: /inventory
 */

import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookRover } from '../types';
import { useInventory } from '../hooks/useInventory';

// ─── Constants ──────────────────────────────────────────────────────────────

const MAX_BOOK_NAME_LENGTH = 200;
const MAX_LANGUAGE_LENGTH = 50;

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatCurrency(amount: number): string {
  return `₹${amount.toFixed(2)}`;
}

// ─── Add/Edit Form ───────────────────────────────────────────────────────────

interface BookFormProps {
  initial?: BookRover.Book;
  onSave: (values: BookRover.BookCreate | BookRover.BookUpdate) => Promise<void>;
  onCancel: () => void;
}

function BookForm({ initial, onSave, onCancel }: BookFormProps) {
  const [bookName, setBookName] = useState(initial?.book_name ?? '');
  const [language, setLanguage] = useState(initial?.language ?? '');
  const [count, setCount] = useState<string>(initial ? '' : '');
  const [costPerBook, setCostPerBook] = useState<string>(
    initial ? String(initial.cost_per_book) : '',
  );
  const [sellingPrice, setSellingPrice] = useState<string>(
    initial ? String(initial.selling_price) : '',
  );
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const isEditMode = Boolean(initial);

  const isValid = useMemo(() => {
    const cost = parseFloat(costPerBook);
    const sell = parseFloat(sellingPrice);
    if (bookName.trim().length === 0 || language.trim().length === 0) return false;
    if (isNaN(cost) || cost <= 0) return false;
    if (isNaN(sell) || sell <= 0) return false;
    if (sell <= cost) return false;
    if (!isEditMode) {
      const cnt = parseInt(count, 10);
      if (isNaN(cnt) || cnt < 1) return false;
    }
    return true;
  }, [bookName, language, count, costPerBook, sellingPrice, isEditMode]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid) return;
    setIsSaving(true);
    setFormError(null);
    try {
      if (isEditMode) {
        await onSave({
          book_name: bookName.trim(),
          language: language.trim(),
          cost_per_book: parseFloat(costPerBook),
          selling_price: parseFloat(sellingPrice),
        } as BookRover.BookUpdate);
      } else {
        await onSave({
          book_name: bookName.trim(),
          language: language.trim(),
          initial_count: parseInt(count, 10),
          cost_per_book: parseFloat(costPerBook),
          selling_price: parseFloat(sellingPrice),
        } as BookRover.BookCreate);
      }
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(detail ?? 'Failed to save. Please try again.');
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="bg-blue-50 border border-blue-200 rounded-xl p-4 space-y-3"
    >
      {formError && (
        <p role="alert" className="text-sm text-red-600 font-medium">
          {formError}
        </p>
      )}

      {isEditMode && initial && (
        <p className="text-sm text-gray-500">
          In Hand: <strong>{initial.current_count}</strong> / Initial:{' '}
          <strong>{initial.initial_count}</strong>
        </p>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="book-name" className="block text-sm font-medium text-gray-700 mb-1">
            Book Name <span className="text-red-500">*</span>
          </label>
          <input
            id="book-name"
            type="text"
            value={bookName}
            onChange={(e) => setBookName(e.target.value)}
            maxLength={MAX_BOOK_NAME_LENGTH}
            placeholder="Thirukkural"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
            Language <span className="text-red-500">*</span>
          </label>
          <input
            id="language"
            type="text"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            maxLength={MAX_LANGUAGE_LENGTH}
            placeholder="Tamil"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {!isEditMode && (
          <div>
            <label htmlFor="count" className="block text-sm font-medium text-gray-700 mb-1">
              Count <span className="text-red-500">*</span>
            </label>
            <input
              id="count"
              type="number"
              min={1}
              value={count}
              onChange={(e) => setCount(e.target.value)}
              placeholder="10"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        <div>
          <label htmlFor="cost-per-book" className="block text-sm font-medium text-gray-700 mb-1">
            Cost per Book (₹) <span className="text-red-500">*</span>
          </label>
          <input
            id="cost-per-book"
            type="number"
            step="0.01"
            min="0.01"
            value={costPerBook}
            onChange={(e) => setCostPerBook(e.target.value)}
            placeholder="50.00"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label
            htmlFor="selling-price"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Selling Price (₹) <span className="text-red-500">*</span>
          </label>
          <input
            id="selling-price"
            type="number"
            step="0.01"
            min="0.01"
            value={sellingPrice}
            onChange={(e) => setSellingPrice(e.target.value)}
            placeholder="75.00"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex gap-3 pt-1">
        <button
          type="submit"
          disabled={!isValid || isSaving}
          className="min-h-[44px] px-5 py-2 rounded-lg bg-blue-600 text-white font-semibold text-base hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSaving ? 'Saving…' : isEditMode ? 'Save Changes' : 'Add Book'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="min-h-[44px] px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-medium text-base hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

// ─── Book Card ───────────────────────────────────────────────────────────────

interface BookCardProps {
  book: BookRover.Book;
  onEdit: (book: BookRover.Book) => void;
  onRemove: (book: BookRover.Book) => void;
}

function BookCard({ book, onEdit, onRemove }: BookCardProps) {
  const isPartiallySold = book.current_count < book.initial_count;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-bold text-gray-900 leading-tight">{book.book_name}</h3>
          <span className="inline-block mt-0.5 text-sm text-gray-500 font-medium">
            {book.language}
          </span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            aria-label={`Edit ${book.book_name}`}
            onClick={() => onEdit(book)}
            className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors text-lg"
          >
            ✏️
          </button>
          <button
            aria-label={`Remove ${book.book_name}`}
            onClick={() => onRemove(book)}
            disabled={isPartiallySold}
            className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-red-50 hover:border-red-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-lg"
          >
            🗑️
          </button>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-gray-700">
        <span>
          In Hand: <strong>{book.current_count}</strong> / Initial:{' '}
          <strong>{book.initial_count}</strong>
        </span>
        <span>
          Cost: <strong>{formatCurrency(book.cost_per_book)}</strong> | Sell:{' '}
          <strong>{formatCurrency(book.selling_price)}</strong>
        </span>
        <span className="col-span-2">
          Cost Balance:{' '}
          <strong className="text-blue-700">
            {formatCurrency(book.current_books_cost_balance)}
          </strong>
        </span>
      </div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function InventoryPage() {
  const navigate = useNavigate();
  const sellerId = localStorage.getItem('bookrover_seller_id') ?? '';

  useEffect(() => {
    if (!sellerId) {
      navigate('/register', { replace: true });
    }
  }, [sellerId, navigate]);

  const { inventory, isLoading, error, clearError, addNewBook, editBook, deleteBook } =
    useInventory(sellerId);

  const [showAddForm, setShowAddForm] = useState(false);
  const [editingBook, setEditingBook] = useState<BookRover.Book | null>(null);
  const [bookToRemove, setBookToRemove] = useState<BookRover.Book | null>(null);
  const [removeError, setRemoveError] = useState<string | null>(null);

  if (!sellerId) return null;

  async function handleAdd(payload: BookRover.BookCreate | BookRover.BookUpdate) {
    await addNewBook(payload as BookRover.BookCreate);
    setShowAddForm(false);
  }

  async function handleEdit(payload: BookRover.BookCreate | BookRover.BookUpdate) {
    if (!editingBook) return;
    await editBook(editingBook.book_id, payload as BookRover.BookUpdate);
    setEditingBook(null);
  }

  async function handleConfirmRemove() {
    if (!bookToRemove) return;
    setRemoveError(null);
    try {
      await deleteBook(bookToRemove.book_id);
      setBookToRemove(null);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setRemoveError(detail ?? 'Failed to remove book.');
    }
  }

  const summary = inventory?.summary;
  const books = inventory?.books ?? [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sticky summary bar */}
      <div className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-lg mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <div className="text-center">
            <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">
              Books in Hand
            </p>
            <p className="text-xl font-bold text-gray-900">
              {summary?.total_books_in_hand ?? 0}
            </p>
          </div>
          <div className="h-10 w-px bg-gray-200" />
          <div className="text-center">
            <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">
              Total Cost Balance
            </p>
            <p className="text-xl font-bold text-blue-700">
              {formatCurrency(summary?.total_cost_balance ?? 0)}
            </p>
          </div>
        </div>
      </div>

      {/* Page content */}
      <div className="max-w-lg mx-auto px-4 py-6 space-y-4">
        {/* Header row */}
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">My Inventory</h1>
          {!showAddForm && !editingBook && (
            <button
              onClick={() => setShowAddForm(true)}
              className="min-h-[44px] px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold text-base hover:bg-blue-700 transition-colors"
            >
              + Add Book
            </button>
          )}
        </div>

        {/* Global error (load failure) */}
        {error && (
          <div
            role="alert"
            className="rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm flex items-start justify-between"
          >
            <span>{error}</span>
            <button onClick={clearError} className="ml-3 font-bold text-red-500">
              ✕
            </button>
          </div>
        )}

        {/* Add Book form */}
        {showAddForm && (
          <BookForm onSave={handleAdd} onCancel={() => setShowAddForm(false)} />
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 rounded-full border-4 border-blue-600 border-t-transparent animate-spin" />
          </div>
        )}

        {/* Book list */}
        {!isLoading && books.length === 0 && !showAddForm && (
          <div className="text-center py-12 text-gray-500 text-base">
            Your inventory is empty. Add your first book using the button above.
          </div>
        )}

        {!isLoading &&
          books.map((book) =>
            editingBook?.book_id === book.book_id ? (
              <BookForm
                key={book.book_id}
                initial={book}
                onSave={handleEdit}
                onCancel={() => setEditingBook(null)}
              />
            ) : (
              <BookCard
                key={book.book_id}
                book={book}
                onEdit={(b) => {
                  setShowAddForm(false);
                  setEditingBook(b);
                }}
                onRemove={(b) => {
                  setRemoveError(null);
                  setBookToRemove(b);
                }}
              />
            ),
          )}
      </div>

      {/* Remove confirmation dialog */}
      {bookToRemove && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
        >
          <div className="w-full max-w-sm bg-white rounded-2xl shadow-xl p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Remove Book?</h2>
            <p className="text-sm text-gray-600 mb-4">
              Remove <strong>{bookToRemove.book_name}</strong> from your inventory? This cannot
              be undone.
            </p>
            {removeError && (
              <p role="alert" className="text-sm text-red-600 mb-3">
                {removeError}
              </p>
            )}
            <div className="flex gap-3">
              <button
                onClick={handleConfirmRemove}
                className="flex-1 min-h-[44px] rounded-lg bg-red-600 text-white font-semibold hover:bg-red-700 transition-colors"
              >
                Remove
              </button>
              <button
                onClick={() => {
                  setBookToRemove(null);
                  setRemoveError(null);
                }}
                className="flex-1 min-h-[44px] rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
