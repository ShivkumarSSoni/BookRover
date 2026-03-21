/**
 * useInventory — custom hook for Seller Inventory CRUD state.
 *
 * Manages all inventory data fetching and mutation for a given seller.
 * Components are pure presentation — they call functions from this hook.
 */

import { useState, useEffect, useCallback } from 'react';
import { BookRover } from '../types';
import {
  fetchInventory,
  addBook,
  updateBook,
  removeBook,
} from '../services/inventoryService';

interface UseInventoryReturn {
  inventory: BookRover.InventoryResponse | null;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
  addNewBook: (payload: BookRover.BookCreate) => Promise<void>;
  editBook: (bookId: string, payload: BookRover.BookUpdate) => Promise<void>;
  deleteBook: (bookId: string) => Promise<void>;
  refresh: () => void;
}

export function useInventory(sellerId: string): UseInventoryReturn {
  const [inventory, setInventory] = useState<BookRover.InventoryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!sellerId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchInventory(sellerId);
      setInventory(data);
    } catch {
      setError('Failed to load inventory. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [sellerId]);

  useEffect(() => {
    load();
  }, [load]);

  const addNewBook = async (payload: BookRover.BookCreate) => {
    const created = await addBook(sellerId, payload);
    setInventory((prev) => {
      if (!prev) return prev;
      const books = [...prev.books, created];
      return {
        ...prev,
        books,
        summary: _recompute(books),
      };
    });
  };

  const editBook = async (bookId: string, payload: BookRover.BookUpdate) => {
    const updated = await updateBook(sellerId, bookId, payload);
    setInventory((prev) => {
      if (!prev) return prev;
      const books = prev.books.map((b) => (b.book_id === bookId ? updated : b));
      return {
        ...prev,
        books,
        summary: _recompute(books),
      };
    });
  };

  const deleteBook = async (bookId: string) => {
    await removeBook(sellerId, bookId);
    setInventory((prev) => {
      if (!prev) return prev;
      const books = prev.books.filter((b) => b.book_id !== bookId);
      return {
        ...prev,
        books,
        summary: _recompute(books),
      };
    });
  };

  return {
    inventory,
    isLoading,
    error,
    clearError: () => setError(null),
    addNewBook,
    editBook,
    deleteBook,
    refresh: load,
  };
}

/** Recompute the summary from the current books list (optimistic update helper). */
function _recompute(books: BookRover.Book[]): BookRover.InventorySummary {
  return {
    total_books_in_hand: books.reduce((sum, b) => sum + b.current_count, 0),
    total_cost_balance: Math.round(
      books.reduce((sum, b) => sum + b.current_books_cost_balance, 0) * 100,
    ) / 100,
    total_initial_cost: Math.round(
      books.reduce((sum, b) => sum + b.total_books_cost_balance, 0) * 100,
    ) / 100,
  };
}
