/**
 * useBookstores — custom hook for BookStore CRUD state.
 *
 * Manages all BookStore data fetching and mutation. Components are pure
 * presentation — they call functions from this hook, never apiClient directly.
 */

import { useState, useEffect, useCallback } from 'react';
import { BookRover } from '../types';
import {
  fetchBookstores,
  createBookstore,
  updateBookstore,
  deleteBookstore,
} from '../services/adminService';

interface UseBookstoresReturn {
  bookstores: BookRover.BookStore[];
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
  addBookstore: (payload: BookRover.BookStoreCreate) => Promise<void>;
  editBookstore: (id: string, payload: BookRover.BookStoreUpdate) => Promise<void>;
  removeBookstore: (id: string) => Promise<void>;
  refresh: () => void;
}

export function useBookstores(): UseBookstoresReturn {
  const [bookstores, setBookstores] = useState<BookRover.BookStore[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchBookstores();
      setBookstores(data);
    } catch {
      setError('Failed to load bookstores. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const addBookstore = async (payload: BookRover.BookStoreCreate) => {
    const created = await createBookstore(payload);
    setBookstores((prev) => [...prev, created]);
  };

  const editBookstore = async (id: string, payload: BookRover.BookStoreUpdate) => {
    const updated = await updateBookstore(id, payload);
    setBookstores((prev) => prev.map((b) => (b.bookstore_id === id ? updated : b)));
  };

  const removeBookstore = async (id: string) => {
    await deleteBookstore(id);
    setBookstores((prev) => prev.filter((b) => b.bookstore_id !== id));
  };

  return {
    bookstores,
    isLoading,
    error,
    clearError: () => setError(null),
    addBookstore,
    editBookstore,
    removeBookstore,
    refresh: load,
  };
}
