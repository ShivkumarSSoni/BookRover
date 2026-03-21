/**
 * ReturnPage — Return unsold books to the bookstore.
 *
 * Shows:
 *   - Bookstore info card (store name, owner, address, phone).
 *   - Read-only table of books to return (current_count > 0 only).
 *   - Summary cards: total unsold books / cost and money to return.
 *   - "Submit Return" button with an inline confirmation step.
 *   - Empty state when all books have been sold.
 *   - Success state after a successful submission.
 *
 * Redirects to /register if no seller is found in SellerContext.
 *
 * Route: /return  (wrapped in SellerProvider in App.tsx)
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSeller } from '../context/SellerContext';
import { useReturn } from '../hooks/useReturn';
import NavBar from '../components/NavBar';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatCurrency(amount: number): string {
  return `₹${amount.toFixed(2)}`;
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function ReturnPage() {
  const navigate = useNavigate();
  const { seller } = useSeller();
  const sellerId = seller?.seller_id ?? '';

  useEffect(() => {
    if (!sellerId) navigate('/register', { replace: true });
  }, [sellerId, navigate]);

  const {
    summary,
    isLoading,
    error,
    isSubmitting,
    submitSuccess,
    submitReturn,
    submitError,
  } = useReturn(sellerId);

  const [confirming, setConfirming] = useState(false);

  // ── Loading ──────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <>
        <NavBar role="seller" />
        <main className="pt-14 min-h-screen bg-gray-50 flex items-center justify-center">
          <p className="text-gray-500 text-sm">Loading return summary…</p>
        </main>
      </>
    );
  }

  // ── Load error ───────────────────────────────────────────────────────────
  if (error || !summary) {
    return (
      <>
        <NavBar role="seller" />
        <main className="pt-14 min-h-screen bg-gray-50 flex items-center justify-center">
          <p className="text-red-600 text-sm">{error ?? 'Could not load return summary.'}</p>
        </main>
      </>
    );
  }

  // ── Success state ────────────────────────────────────────────────────────
  if (submitSuccess) {
    return (
      <>
        <NavBar role="seller" />
        <main className="pt-14 min-h-screen bg-gray-50">
          <div className="max-w-lg mx-auto px-4 py-8">
            <div
              data-testid="success-banner"
              className="bg-green-50 border border-green-200 rounded-xl p-6 text-center"
            >
              <p className="text-green-800 font-semibold text-base">
                Return submitted successfully!
              </p>
              <p className="text-green-700 text-sm mt-1">
                Your inventory has been cleared and your status has been reset.
              </p>
            </div>
          </div>
        </main>
      </>
    );
  }

  const { bookstore, books_to_return, total_books_to_return, total_cost_of_unsold_books, total_money_collected_from_sales } = summary;
  const hasBooks = books_to_return.length > 0;

  // ── Main render ──────────────────────────────────────────────────────────
  return (
    <>
      <NavBar role="seller" />
      <main className="pt-14 min-h-screen bg-gray-50">
        <div className="max-w-lg mx-auto px-4 py-6 space-y-6">

          {/* Bookstore info card */}
          <section
            aria-label="Bookstore information"
            className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-1"
          >
            <p className="text-base font-semibold text-gray-900">
              Returning to: {bookstore.store_name}
            </p>
            <p className="text-sm text-gray-600">Owner: {bookstore.owner_name}</p>
            <p className="text-sm text-gray-600">Address: {bookstore.address}</p>
            <p className="text-sm text-gray-600">Phone: {bookstore.phone_number}</p>
          </section>

          {/* Books table — only shown when there are books to return */}
          {hasBooks ? (
            <section aria-label="Books to return">
              <h2 className="text-sm font-semibold text-gray-700 mb-2">Books to Return</h2>
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Book Name</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Language</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-600">Qty</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-600">Cost</th>
                      <th className="text-right px-4 py-3 font-medium text-gray-600">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {books_to_return.map((book) => (
                      <tr key={book.book_id}>
                        <td className="px-4 py-3 text-gray-900">{book.book_name}</td>
                        <td className="px-4 py-3 text-gray-600">{book.language}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{book.quantity_to_return}</td>
                        <td className="px-4 py-3 text-right text-gray-600">{formatCurrency(book.cost_per_book)}</td>
                        <td className="px-4 py-3 text-right font-medium text-gray-900">{formatCurrency(book.total_cost)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ) : (
            /* Empty state — all books sold */
            <section
              data-testid="empty-state"
              className="bg-green-50 border border-green-200 rounded-xl p-6 text-center space-y-1"
            >
              <p className="text-green-800 font-semibold text-base">All books sold!</p>
              <p className="text-green-700 text-sm">Nothing to return.</p>
              <p className="text-green-700 text-sm">
                Your money to return: {formatCurrency(total_money_collected_from_sales)}
              </p>
            </section>
          )}

          {/* Summary cards */}
          <section aria-label="Return summary" className="grid grid-cols-2 gap-3">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 text-center">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Unsold Books</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{total_books_to_return}</p>
              <p className="text-sm text-gray-500 mt-0.5">Cost: {formatCurrency(total_cost_of_unsold_books)}</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 text-center">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Money to Return</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                {formatCurrency(total_money_collected_from_sales)}
              </p>
            </div>
          </section>

          {/* Submit error banner */}
          {submitError && (
            <div
              data-testid="submit-error"
              className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-red-700 text-sm"
            >
              {submitError}
            </div>
          )}

          {/* Confirmation flow or Submit button */}
          {confirming ? (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 space-y-4">
              <p className="text-amber-900 text-sm font-medium">
                Are you sure? This will clear your entire inventory and cannot be undone.
              </p>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setConfirming(false)}
                  className="flex-1 min-h-[44px] px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-700 text-sm font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => submitReturn()}
                  disabled={isSubmitting}
                  className="flex-1 min-h-[44px] px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-60 text-white text-sm font-semibold transition-colors"
                >
                  {isSubmitting ? 'Submitting…' : 'Confirm Return'}
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setConfirming(true)}
              className="w-full min-h-[44px] px-4 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-base font-semibold transition-colors shadow-sm"
            >
              Submit Return
            </button>
          )}

        </div>
      </main>
    </>
  );
}
