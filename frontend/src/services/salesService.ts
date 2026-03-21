/**
 * Sales API service — all HTTP calls for the New Buyer / Sales feature.
 *
 * This is the only place components may trigger network requests related
 * to the Sales feature. Components call these functions via custom hooks —
 * never import apiClient directly in a component.
 */

import apiClient from './apiClient';
import { BookRover } from '../types';

/**
 * Record a new sale for a seller.
 */
export async function createSale(
  sellerId: string,
  payload: BookRover.SaleCreate,
): Promise<BookRover.SaleResponse> {
  const response = await apiClient.post<BookRover.SaleResponse>(
    `/sellers/${sellerId}/sales`,
    payload,
  );
  return response.data;
}

/**
 * Fetch all sales for a seller.
 */
export async function fetchSales(sellerId: string): Promise<BookRover.SaleResponse[]> {
  const response = await apiClient.get<BookRover.SaleResponse[]>(
    `/sellers/${sellerId}/sales`,
  );
  return response.data;
}

/**
 * Fetch a single sale record by ID.
 */
export async function fetchSale(
  sellerId: string,
  saleId: string,
): Promise<BookRover.SaleResponse> {
  const response = await apiClient.get<BookRover.SaleResponse>(
    `/sellers/${sellerId}/sales/${saleId}`,
  );
  return response.data;
}
