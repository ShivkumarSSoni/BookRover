/**
 * Inventory API service — all HTTP calls for Seller Inventory.
 *
 * This is the only place components may trigger network requests related
 * to the Inventory feature. Components call these functions via custom hooks —
 * never import apiClient directly in a component.
 */

import apiClient from './apiClient';
import { BookRover } from '../types';

/**
 * Fetch the full inventory (books + summary) for a seller.
 */
export async function fetchInventory(sellerId: string): Promise<BookRover.InventoryResponse> {
  const response = await apiClient.get<BookRover.InventoryResponse>(
    `/sellers/${sellerId}/inventory`,
  );
  return response.data;
}

/**
 * Add a new book to a seller's inventory.
 */
export async function addBook(
  sellerId: string,
  payload: BookRover.BookCreate,
): Promise<BookRover.Book> {
  const response = await apiClient.post<BookRover.Book>(
    `/sellers/${sellerId}/inventory`,
    payload,
  );
  return response.data;
}

/**
 * Update a book in a seller's inventory.
 */
export async function updateBook(
  sellerId: string,
  bookId: string,
  payload: BookRover.BookUpdate,
): Promise<BookRover.Book> {
  const response = await apiClient.put<BookRover.Book>(
    `/sellers/${sellerId}/inventory/${bookId}`,
    payload,
  );
  return response.data;
}

/**
 * Remove a book from a seller's inventory.
 */
export async function removeBook(sellerId: string, bookId: string): Promise<void> {
  await apiClient.delete(`/sellers/${sellerId}/inventory/${bookId}`);
}
