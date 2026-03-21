/**
 * Admin API service — all HTTP calls for BookStore and GroupLeader.
 *
 * This is the only place components may trigger network requests related
 * to the Admin feature. Components call these functions via custom hooks —
 * never import apiClient directly in a component.
 */

import apiClient from './apiClient';
import { BookRover } from '../types';

// ── BookStore endpoints ───────────────────────────────────────────────────────

export async function fetchBookstores(): Promise<BookRover.BookStore[]> {
  const response = await apiClient.get<BookRover.BookStore[]>('/admin/bookstores');
  return response.data;
}

export async function createBookstore(
  payload: BookRover.BookStoreCreate,
): Promise<BookRover.BookStore> {
  const response = await apiClient.post<BookRover.BookStore>('/admin/bookstores', payload);
  return response.data;
}

export async function updateBookstore(
  bookstoreId: string,
  payload: BookRover.BookStoreUpdate,
): Promise<BookRover.BookStore> {
  const response = await apiClient.put<BookRover.BookStore>(
    `/admin/bookstores/${bookstoreId}`,
    payload,
  );
  return response.data;
}

export async function deleteBookstore(bookstoreId: string): Promise<void> {
  await apiClient.delete(`/admin/bookstores/${bookstoreId}`);
}

// ── GroupLeader endpoints ─────────────────────────────────────────────────────

export async function fetchGroupLeaders(): Promise<BookRover.GroupLeader[]> {
  const response = await apiClient.get<BookRover.GroupLeader[]>('/admin/group-leaders');
  return response.data;
}

export async function createGroupLeader(
  payload: BookRover.GroupLeaderCreate,
): Promise<BookRover.GroupLeader> {
  const response = await apiClient.post<BookRover.GroupLeader>(
    '/admin/group-leaders',
    payload,
  );
  return response.data;
}

export async function updateGroupLeader(
  groupLeaderId: string,
  payload: BookRover.GroupLeaderUpdate,
): Promise<BookRover.GroupLeader> {
  const response = await apiClient.put<BookRover.GroupLeader>(
    `/admin/group-leaders/${groupLeaderId}`,
    payload,
  );
  return response.data;
}

export async function deleteGroupLeader(groupLeaderId: string): Promise<void> {
  await apiClient.delete(`/admin/group-leaders/${groupLeaderId}`);
}
