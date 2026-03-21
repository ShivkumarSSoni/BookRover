/**
 * NewBuyerPage — Record a new sale for a buyer.
 *
 * Allows the seller to:
 *   1. Select books from their inventory using +/- quantity buttons.
 *   2. Fill in buyer contact details (name, country code, phone).
 *   3. Submit the sale — inventory is decremented on success.
 *
 * A sticky running-total bar shows selected book count and total amount.
 * Success shows a green banner (auto-dismissed after 3 s).
 * Errors show a dismissible red banner.
 *
 * Route: /new-buyer  (wrapped in SellerProvider in App.tsx)
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSeller } from '../context/SellerContext';
import { useSales } from '../hooks/useSales';
import NavBar from '../components/NavBar';

// ─── Constants ───────────────────────────────────────────────────────────────

const DEFAULT_COUNTRY_CODE = '+91';
const SUCCESS_DISMISS_MS = 3000;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatCurrency(amount: number): string {
  return `₹${amount.toFixed(2)}`;
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function NewBuyerPage() {
  const navigate = useNavigate();
  const { seller } = useSeller();
  const sellerId = seller?.seller_id ?? '';

  useEffect(() => {
    if (!sellerId) navigate('/register', { replace: true });
  }, [sellerId, navigate]);

  const {
    books,
    isLoadingInventory,
    inventoryError,
    quantities,
    totalBooksSelected,
    totalAmount,
    incrementQty,
    decrementQty,
    resetAll,
    submitSale,
    isSubmitting,
  } = useSales(sellerId);

  // ── Buyer form state ─────────────────────────────────────────────────────
  const [buyerFirstName, setBuyerFirstName] = useState('');
  const [buyerLastName, setBuyerLastName] = useState('');
  const [buyerCountryCode, setBuyerCountryCode] = useState(DEFAULT_COUNTRY_CODE);
  const [buyerPhone, setBuyerPhone] = useState('');

  // ── Page-level feedback ──────────────────────────────────────────────────
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const isBuyerValid =
    buyerFirstName.trim().length > 0 &&
    buyerLastName.trim().length > 0 &&
    buyerCountryCode.trim().length >= 2 &&
    /^\d{5,15}$/.test(buyerPhone);

  const canSubmit = totalBooksSelected > 0 && isBuyerValid && !isSubmitting;

  const handleClear = useCallback(() => {
    resetAll();
    setBuyerFirstName('');
    setBuyerLastName('');
    setBuyerCountryCode(DEFAULT_COUNTRY_CODE);
    setBuyerPhone('');
    setSubmitError(null);
  }, [resetAll]);

  const handleSubmit = useCallback(async () => {
    setSubmitError(null);
    try {
      const sale = await submitSale({
        buyer_first_name: buyerFirstName.trim(),
        buyer_last_name: buyerLastName.trim(),
        buyer_country_code: buyerCountryCode.trim(),
        buyer_phone: buyerPhone.trim(),
      });
      const msg = `Sale saved! ✓ ${sale.total_books_sold} book${sale.total_books_sold > 1 ? 's' : ''} — ${formatCurrency(sale.total_amount_collected)}`;
      setSuccessMessage(msg);
      handleClear();
      setTimeout(() => setSuccessMessage(null), SUCCESS_DISMISS_MS);
    } catch (err: unknown) {
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setSubmitError(detail ?? 'Failed to record sale. Please try again.');
    }
  }, [submitSale, buyerFirstName, buyerLastName, buyerCountryCode, buyerPhone, handleClear]);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar role="seller" />
      <div className="pt-14">
        <div className="max-w-lg mx-auto px-4 py-6 space-y-6">

          {/* Page header */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">New Buyer</h1>
            {seller && (
              <p className="mt-1 text-sm text-gray-500">
                Selling as: {seller.first_name} {seller.last_name}
              </p>
            )}
          </div>

          {/* Success banner */}
          {successMessage && (
            <div
              role="status"
              aria-live="polite"
              className="rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-green-800 text-sm font-medium"
            >
              {successMessage}
            </div>
          )}

          {/* Error banner */}
          {submitError && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 flex items-start justify-between gap-3">
              <p className="text-red-800 text-sm">{submitError}</p>
              <button
                type="button"
                aria-label="Dismiss error"
                onClick={() => setSubmitError(null)}
                className="text-red-500 hover:text-red-700 flex-shrink-0 text-lg leading-none"
              >
                ×
              </button>
            </div>
          )}

          {/* ── Section 1: Select Books ─────────────────────────────────── */}
          <section aria-labelledby="books-heading">
            <h2 id="books-heading" className="text-lg font-semibold text-gray-800 mb-3">
              Select Books to Sell
            </h2>

            {isLoadingInventory ? (
              <p className="text-sm text-gray-500">Loading inventory…</p>
            ) : inventoryError ? (
              <p className="text-sm text-red-600">{inventoryError}</p>
            ) : books.length === 0 ? (
              <p className="text-sm text-gray-500">No books available in inventory.</p>
            ) : (
              <ul className="space-y-3">
                {books.map((book) => {
                  const qty = quantities[book.book_id] ?? 0;
                  return (
                    <li
                      key={book.book_id}
                      className="bg-white rounded-xl border border-gray-200 px-4 py-3 flex items-center justify-between gap-3"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-gray-900 truncate">{book.book_name}</p>
                        <p className="text-sm text-gray-500">
                          {book.language} · {formatCurrency(book.selling_price)} · {book.current_count} left
                        </p>
                      </div>

                      {/* Quantity controls */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          type="button"
                          aria-label={`Decrease quantity of ${book.book_name}`}
                          onClick={() => decrementQty(book.book_id)}
                          disabled={qty === 0}
                          className="w-9 h-9 rounded-full border border-gray-300 text-gray-700 font-bold text-lg disabled:opacity-30 flex items-center justify-center hover:bg-gray-100 active:bg-gray-200"
                        >
                          −
                        </button>
                        <span
                          aria-label={`Quantity for ${book.book_name}`}
                          className="w-8 text-center text-base font-semibold text-gray-900 tabular-nums"
                        >
                          {qty}
                        </span>
                        <button
                          type="button"
                          aria-label={`Increase quantity of ${book.book_name}`}
                          onClick={() => incrementQty(book.book_id)}
                          disabled={qty >= book.current_count}
                          className="w-9 h-9 rounded-full border border-gray-300 text-gray-700 font-bold text-lg disabled:opacity-30 flex items-center justify-center hover:bg-gray-100 active:bg-gray-200"
                        >
                          +
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}

            {/* Running total bar */}
            {totalBooksSelected > 0 && (
              <div className="mt-4 rounded-lg bg-blue-50 border border-blue-200 px-4 py-3 flex items-center justify-between">
                <span className="text-sm font-medium text-blue-800">
                  Books: {totalBooksSelected}
                </span>
                <span className="text-sm font-semibold text-blue-900">
                  Total: {formatCurrency(totalAmount)}
                </span>
              </div>
            )}
          </section>

          {/* ── Section 2: Buyer Information ────────────────────────────── */}
          <section aria-labelledby="buyer-heading">
            <h2 id="buyer-heading" className="text-lg font-semibold text-gray-800 mb-3">
              Buyer Information
            </h2>

            <div className="bg-white rounded-xl border border-gray-200 px-4 py-4 space-y-4">
              {/* First name */}
              <div>
                <label htmlFor="buyer-first-name" className="block text-sm font-medium text-gray-700 mb-1">
                  First Name
                </label>
                <input
                  id="buyer-first-name"
                  type="text"
                  value={buyerFirstName}
                  onChange={(e) => setBuyerFirstName(e.target.value)}
                  maxLength={50}
                  placeholder="First name"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Last name */}
              <div>
                <label htmlFor="buyer-last-name" className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name
                </label>
                <input
                  id="buyer-last-name"
                  type="text"
                  value={buyerLastName}
                  onChange={(e) => setBuyerLastName(e.target.value)}
                  maxLength={50}
                  placeholder="Last name"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Phone number */}
              <div>
                <label htmlFor="buyer-phone" className="block text-sm font-medium text-gray-700 mb-1">
                  Phone Number
                </label>
                <div className="flex gap-2">
                  <input
                    id="buyer-country-code"
                    type="text"
                    value={buyerCountryCode}
                    onChange={(e) => setBuyerCountryCode(e.target.value)}
                    maxLength={5}
                    aria-label="Country code"
                    className="w-20 rounded-lg border border-gray-300 px-3 py-2 text-base text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    id="buyer-phone"
                    type="tel"
                    inputMode="numeric"
                    value={buyerPhone}
                    onChange={(e) => setBuyerPhone(e.target.value.replace(/\D/g, ''))}
                    maxLength={15}
                    placeholder="Phone number"
                    className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* ── Section 3: Actions ────────────────────────────────────────── */}
          <div className="flex gap-3 pb-6">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="flex-1 min-h-[44px] rounded-xl bg-blue-600 text-white font-semibold text-base disabled:opacity-40 hover:bg-blue-700 active:bg-blue-800 transition-colors"
            >
              {isSubmitting ? 'Saving…' : 'Save Sale'}
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="px-5 min-h-[44px] rounded-xl border border-gray-300 text-gray-700 font-medium text-base hover:bg-gray-100 active:bg-gray-200 transition-colors"
            >
              Clear
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
