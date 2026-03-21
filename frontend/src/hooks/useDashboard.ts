/**
 * useDashboard — custom hook for the Group Leader Dashboard.
 *
 * Manages:
 *   - Fetching the list of bookstores the GL is linked to (via /lookup/group-leaders).
 *   - The currently selected bookstore (defaults to the first in the list,
 *     or the last selection stored in sessionStorage).
 *   - Dashboard data fetch + re-fetch when bookstore or sort params change.
 *   - Sort state: sort_by field and sort_order direction.
 */

import { useState, useEffect, useCallback } from 'react';
import { BookRover } from '../types';
import { fetchGroupLeaderLookup } from '../services/sellerService';
import { fetchDashboard } from '../services/dashboardService';

const SESSION_KEY_BOOKSTORE = 'bookrover_gl_selected_bookstore';

interface UseDashboardReturn {
  dashboard: BookRover.DashboardResponse | null;
  bookstores: BookRover.BookStoreSummary[];
  selectedBookstoreId: string | null;
  isLoading: boolean;
  error: string | null;
  sortBy: BookRover.DashboardSortBy;
  sortOrder: BookRover.DashboardSortOrder;
  selectBookstore: (bookstoreId: string) => void;
  toggleSort: (field: BookRover.DashboardSortBy) => void;
}

export function useDashboard(groupLeaderId: string | null): UseDashboardReturn {
  const [bookstores, setBookstores] = useState<BookRover.BookStoreSummary[]>([]);
  const [selectedBookstoreId, setSelectedBookstoreId] = useState<string | null>(
    sessionStorage.getItem(SESSION_KEY_BOOKSTORE),
  );
  const [dashboard, setDashboard] = useState<BookRover.DashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<BookRover.DashboardSortBy>('total_amount_collected');
  const [sortOrder, setSortOrder] = useState<BookRover.DashboardSortOrder>('desc');

  // ── Step 1: Resolve available bookstores for this group leader ──────────────
  useEffect(() => {
    if (!groupLeaderId) return;

    fetchGroupLeaderLookup()
      .then((leaders) => {
        const me = leaders.find((l) => l.group_leader_id === groupLeaderId);
        if (!me) return;
        setBookstores(me.bookstores);
        // If no bookstore is selected yet (or stored one is stale), default to first
        setSelectedBookstoreId((prev) => {
          const valid = me.bookstores.find((b) => b.bookstore_id === prev);
          if (valid) return prev;
          return me.bookstores[0]?.bookstore_id ?? null;
        });
      })
      .catch(() => {
        setError('Failed to load bookstore list.');
      });
  }, [groupLeaderId]);

  // ── Step 2: Fetch dashboard whenever dependencies change ────────────────────
  const load = useCallback(async () => {
    if (!groupLeaderId || !selectedBookstoreId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchDashboard(groupLeaderId, selectedBookstoreId, sortBy, sortOrder);
      setDashboard(data);
    } catch {
      setError('Failed to load dashboard. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [groupLeaderId, selectedBookstoreId, sortBy, sortOrder]);

  useEffect(() => {
    load();
  }, [load]);

  const selectBookstore = useCallback((bookstoreId: string) => {
    sessionStorage.setItem(SESSION_KEY_BOOKSTORE, bookstoreId);
    setSelectedBookstoreId(bookstoreId);
  }, []);

  const toggleSort = useCallback((field: BookRover.DashboardSortBy) => {
    setSortBy((prev) => {
      if (prev !== field) {
        setSortOrder('asc');
        return field;
      }
      setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'));
      return field;
    });
  }, []);

  return {
    dashboard,
    bookstores,
    selectedBookstoreId,
    isLoading,
    error,
    sortBy,
    sortOrder,
    selectBookstore,
    toggleSort,
  };
}
