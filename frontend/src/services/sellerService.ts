/**
 * Seller API service — HTTP calls for Seller registration and Lookup.
 *
 * This is the only place components may trigger network requests related
 * to the Seller Registration feature. Components call these functions via
 * custom hooks — never import apiClient directly in a component.
 */

import apiClient from './apiClient';
import { BookRover } from '../types';

/**
 * Fetch all group leaders with their linked bookstores.
 * Used to populate the registration dropdown.
 */
export async function fetchGroupLeaderLookup(): Promise<BookRover.GroupLeaderLookup[]> {
  const response = await apiClient.get<BookRover.GroupLeaderLookup[]>('/lookup/group-leaders');
  return response.data;
}

/**
 * Register a new seller.
 *
 * @param payload - SellerCreate fields from the registration form.
 * @returns The created Seller record.
 */
export async function registerSeller(payload: BookRover.SellerCreate): Promise<BookRover.Seller> {
  const response = await apiClient.post<BookRover.Seller>('/sellers', payload);
  return response.data;
}

/**
 * Fetch a seller profile by ID.
 *
 * @param sellerId - The seller's UUID.
 * @returns The Seller record.
 */
export async function fetchSeller(sellerId: string): Promise<BookRover.Seller> {
  const response = await apiClient.get<BookRover.Seller>(`/sellers/${sellerId}`);
  return response.data;
}
