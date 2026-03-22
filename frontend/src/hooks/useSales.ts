/**
 * useSales — custom hook for the New Buyer sale recording flow.
 *
 * Manages:
 *   - Inventory fetch on mount (only books with current_count > 0 are selectable).
 *   - Per-book quantity state (quantities map: book_id → number).
 *   - Running totals (totalBooksSelected, totalAmount).
 *   - Sale submission and success/error state.
 */

import { useState, useEffect, useCallback } from 'react';
import { BookRover } from '../types';
import { fetchInventory } from '../services/inventoryService';
import { createSale } from '../services/salesService';

interface UseSalesReturn {
  books: BookRover.Book[];
  isLoadingInventory: boolean;
  inventoryError: string | null;
  quantities: Record<string, number>;
  totalBooksSelected: number;
  totalAmount: number;
  incrementQty: (bookId: string) => void;
  decrementQty: (bookId: string) => void;
  resetAll: () => void;
  submitSale: (buyerDetails: Omit<BookRover.SaleCreate, 'items'>) => Promise<BookRover.SaleResponse>;
  isSubmitting: boolean;
}

export function useSales(sellerId: string): UseSalesReturn {
  const [books, setBooks] = useState<BookRover.Book[]>([]);
  const [isLoadingInventory, setIsLoadingInventory] = useState(true);
  const [inventoryError, setInventoryError] = useState<string | null>(null);
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadInventory = useCallback(async () => {
    if (!sellerId) return;
    setIsLoadingInventory(true);
    setInventoryError(null);
    try {
      const data = await fetchInventory(sellerId);
      const available = data.books.filter((b) => b.current_count > 0);
      setBooks(available);
    } catch {
      setInventoryError('Failed to load inventory. Please try again.');
    } finally {
      setIsLoadingInventory(false);
    }
  }, [sellerId]);

  useEffect(() => {
    loadInventory();
  }, [loadInventory]);

  const incrementQty = useCallback(
    (bookId: string) => {
      const book = books.find((b) => b.book_id === bookId);
      if (!book) return;
      setQuantities((prev) => {
        const current = prev[bookId] ?? 0;
        if (current >= book.current_count) return prev;
        return { ...prev, [bookId]: current + 1 };
      });
    },
    [books],
  );

  const decrementQty = useCallback((bookId: string) => {
    setQuantities((prev) => {
      const current = prev[bookId] ?? 0;
      if (current <= 0) return prev;
      return { ...prev, [bookId]: current - 1 };
    });
  }, []);

  const resetAll = useCallback(() => {
    setQuantities({});
  }, []);

  const totalBooksSelected = Object.values(quantities).reduce((sum, q) => sum + q, 0);

  const totalAmount = books.reduce((sum, book) => {
    const qty = quantities[book.book_id] ?? 0;
    return sum + qty * book.selling_price;
  }, 0);

  const submitSale = useCallback(
    async (buyerDetails: Omit<BookRover.SaleCreate, 'items'>): Promise<BookRover.SaleResponse> => {
      const items: BookRover.SaleItemCreate[] = Object.entries(quantities)
        .filter(([, qty]) => qty > 0)
        .map(([book_id, quantity_sold]) => ({ book_id, quantity_sold }));

      setIsSubmitting(true);
      try {
        const sale = await createSale(sellerId, { ...buyerDetails, items });
        // Refresh inventory counts so the next buyer sees accurate stock.
        await loadInventory();
        return sale;
      } finally {
        setIsSubmitting(false);
      }
    },
    [sellerId, quantities, loadInventory],
  );

  return {
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
  };
}
