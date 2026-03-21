/**
 * Return API service — HTTP calls for the Seller Return Books feature.
 *
 * Provides two operations:
 *   - fetchReturnSummary: retrieves books to return and financial totals.
 *   - submitReturn: persists the return, clears inventory, resets seller status.
 *
 * Components call these functions via the useReturn hook — never directly.
 */

import apiClient from './apiClient';
import { BookRover } from '../types';

/**
 * Fetch the return summary for a seller.
 *
 * @param sellerId - The seller's UUID.
 * @returns ReturnSummaryResponse with bookstore info, books to return, and totals.
 */
export async function fetchReturnSummary(
  sellerId: string,
): Promise<BookRover.ReturnSummaryResponse> {
  const response = await apiClient.get<BookRover.ReturnSummaryResponse>(
    `/sellers/${sellerId}/return-summary`,
  );
  return response.data;
}

/**
 * Submit a return for a seller.
 *
 * @param sellerId - The seller's UUID.
 * @param notes - Optional notes about the return.
 * @returns ReturnResponse with return details.
 */
export async function submitReturn(
  sellerId: string,
  notes?: string,
): Promise<BookRover.ReturnResponse> {
  const response = await apiClient.post<BookRover.ReturnResponse>(
    `/sellers/${sellerId}/returns`,
    { notes: notes ?? null },
  );
  return response.data;
}
