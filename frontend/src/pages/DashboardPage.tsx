/**
 * DashboardPage — Group Leader performance dashboard.
 *
 * Shows all sellers under the group leader for a selected bookstore,
 * with their total books sold and total amount collected.
 *
 * Features:
 *   - Summary cards: total sellers + total amount collected.
 *   - Bookstore selector (Change button) when group leader has multiple bookstores.
 *   - Sortable sellers table: click "Books Sold" or "Money Collected" column
 *     headers to toggle sort (first tap: asc, second tap: desc).
 *   - Active sort column shows ↑ or ↓ indicator.
 *   - Totals row always at the bottom.
 *   - Empty state when no sellers are registered.
 *
 * Route: /dashboard  (wrapped in GroupLeaderProvider in App.tsx)
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGroupLeader } from '../context/GroupLeaderContext';
import { useDashboard } from '../hooks/useDashboard';
import NavBar from '../components/NavBar';
import { BookRover } from '../types';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatCurrency(amount: number): string {
  return `₹${amount.toFixed(2)}`;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

interface SortHeaderProps {
  label: string;
  field: BookRover.DashboardSortBy;
  activeSortBy: BookRover.DashboardSortBy;
  activeSortOrder: BookRover.DashboardSortOrder;
  onToggle: (field: BookRover.DashboardSortBy) => void;
}

function SortHeader({ label, field, activeSortBy, activeSortOrder, onToggle }: SortHeaderProps) {
  const isActive = activeSortBy === field;
  const arrow = isActive ? (activeSortOrder === 'asc' ? ' ↑' : ' ↓') : '';

  return (
    <th
      scope="col"
      className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-800"
      onClick={() => onToggle(field)}
      aria-sort={isActive ? (activeSortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}
    >
      {label}{arrow}
    </th>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function DashboardPage() {
  const navigate = useNavigate();
  const { groupLeaderId } = useGroupLeader();

  useEffect(() => {
    if (!groupLeaderId) navigate('/register', { replace: true });
  }, [groupLeaderId, navigate]);

  const {
    dashboard,
    bookstores,
    selectedBookstoreId,
    isLoading,
    error,
    sortBy,
    sortOrder,
    selectBookstore,
    toggleSort,
  } = useDashboard(groupLeaderId);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar role="group-leader" />
      <div className="pt-14">
        <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">

          {/* ── Header ──────────────────────────────────────────────── */}
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              {dashboard && (
                <>
                  <p className="text-sm text-gray-500">Group Leader</p>
                  <h1 className="text-xl font-bold text-gray-900">
                    {dashboard.group_leader.name}
                  </h1>
                </>
              )}
              {!dashboard && !isLoading && (
                <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
              )}
            </div>

            {/* Bookstore context + optional Change button */}
            {dashboard && (
              <div className="text-right">
                <p className="text-sm text-gray-500">Bookstore</p>
                <p className="font-medium text-gray-900">{dashboard.bookstore.store_name}</p>
                {bookstores.length > 1 && (
                  <div className="mt-1 flex flex-wrap gap-1 justify-end">
                    {bookstores.map((bs) => (
                      <button
                        key={bs.bookstore_id}
                        type="button"
                        onClick={() => selectBookstore(bs.bookstore_id)}
                        className={[
                          'min-h-[32px] px-3 py-1 rounded-lg text-xs font-medium border transition-colors',
                          bs.bookstore_id === selectedBookstoreId
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50',
                        ].join(' ')}
                      >
                        {bs.store_name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Error banner ──────────────────────────────────────────── */}
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-red-800 text-sm">
              {error}
            </div>
          )}

          {/* ── Loading ───────────────────────────────────────────────── */}
          {isLoading && (
            <div className="text-center py-12 text-gray-500 text-sm">Loading dashboard…</div>
          )}

          {/* ── Content ───────────────────────────────────────────────── */}
          {dashboard && !isLoading && (
            <>
              {/* Summary cards */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white rounded-xl border border-gray-200 px-4 py-4">
                  <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">
                    Total Sellers
                  </p>
                  <p className="mt-1 text-3xl font-bold text-gray-900">
                    {dashboard.sellers.length}
                  </p>
                </div>
                <div className="bg-white rounded-xl border border-gray-200 px-4 py-4">
                  <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">
                    Total Collected
                  </p>
                  <p className="mt-1 text-3xl font-bold text-gray-900">
                    {formatCurrency(dashboard.totals.total_amount_collected)}
                  </p>
                </div>
              </div>

              {/* Sellers table */}
              {dashboard.sellers.length === 0 ? (
                <p className="text-center py-12 text-sm text-gray-500">
                  No sellers registered under you yet.
                </p>
              ) : (
                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th
                          scope="col"
                          className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                        >
                          Seller Name
                        </th>
                        <SortHeader
                          label="Books Sold"
                          field="total_books_sold"
                          activeSortBy={sortBy}
                          activeSortOrder={sortOrder}
                          onToggle={toggleSort}
                        />
                        <SortHeader
                          label="Money Collected"
                          field="total_amount_collected"
                          activeSortBy={sortBy}
                          activeSortOrder={sortOrder}
                          onToggle={toggleSort}
                        />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {dashboard.sellers.map((row) => (
                        <tr key={row.seller_id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium text-gray-900">{row.full_name}</td>
                          <td className="px-4 py-3 text-right text-gray-700 tabular-nums">
                            {row.total_books_sold}
                          </td>
                          <td className="px-4 py-3 text-right text-gray-700 tabular-nums">
                            {formatCurrency(row.total_amount_collected)}
                          </td>
                        </tr>
                      ))}

                      {/* Totals row */}
                      <tr className="bg-gray-50 font-semibold border-t-2 border-gray-200">
                        <td className="px-4 py-3 text-gray-900">Total</td>
                        <td className="px-4 py-3 text-right text-gray-900 tabular-nums">
                          {dashboard.totals.total_books_sold}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-900 tabular-nums">
                          {formatCurrency(dashboard.totals.total_amount_collected)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

        </div>
      </div>
    </div>
  );
}
