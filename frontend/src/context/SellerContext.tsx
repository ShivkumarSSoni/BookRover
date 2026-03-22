/**
 * SellerContext — React context that holds the current seller's profile.
 *
 * Reads the seller_id from AuthContext (me.seller_id), then fetches the full
 * seller profile once from GET /sellers/{seller_id}. All seller pages
 * (Inventory, New Buyer, Return) consume this context to access the seller's
 * name and bookstore without making repeated API calls.
 *
 * Usage:
 *   - Wrap seller routes in <SellerProvider> inside App.tsx.
 *   - Read seller profile in any component via useSeller().
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { BookRover } from '../types';
import { fetchSeller } from '../services/sellerService';
import { useAuth } from './AuthContext';

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
  const { me, isLoading: authLoading } = useAuth();
  const [seller, setSeller] = useState<BookRover.Seller | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    const sellerId = me?.seller_id;
    if (!sellerId) {
      setIsLoading(false);
      return;
    }
    fetchSeller(sellerId)
      .then(setSeller)
      .catch(() => {
        // Profile fetch failed — pages will handle redirect via RequireRole guard.
      })
      .finally(() => setIsLoading(false));
  }, [me, authLoading]);

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
