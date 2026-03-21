/**
 * SellerContext — React context that holds the current seller's profile.
 *
 * Fetches the seller profile once from GET /sellers/{seller_id} using the
 * seller_id stored in localStorage. All seller pages (Inventory, New Buyer,
 * Return) consume this context to access the seller's name and bookstore
 * without making repeated API calls.
 *
 * Usage:
 *   - Wrap seller routes in <SellerProvider> inside App.tsx.
 *   - Read seller profile in any component via useSeller().
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { BookRover } from '../types';
import { fetchSeller } from '../services/sellerService';

// ─── Context shape ────────────────────────────────────────────────────────────

interface SellerContextValue {
  seller: BookRover.Seller | null;
  isLoading: boolean;
}

const SellerContext = createContext<SellerContextValue | null>(null);

// ─── Provider ─────────────────────────────────────────────────────────────────

interface SellerProviderProps {
  children: ReactNode;
}

export function SellerProvider({ children }: SellerProviderProps) {
  const [seller, setSeller] = useState<BookRover.Seller | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const sellerId = localStorage.getItem('bookrover_seller_id');
    if (!sellerId) {
      setIsLoading(false);
      return;
    }
    fetchSeller(sellerId)
      .then(setSeller)
      .catch(() => {
        // Profile fetch failed — pages will handle redirect via sellerId guard
      })
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <SellerContext.Provider value={{ seller, isLoading }}>
      {children}
    </SellerContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

/**
 * Returns the current seller context value.
 * Must be used inside a <SellerProvider>.
 */
export function useSeller(): SellerContextValue {
  const ctx = useContext(SellerContext);
  if (!ctx) {
    throw new Error('useSeller must be used within a SellerProvider');
  }
  return ctx;
}
