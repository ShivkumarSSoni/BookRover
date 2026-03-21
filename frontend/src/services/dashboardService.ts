/**
 * Dashboard API service — HTTP calls for the Group Leader Dashboard.
 *
 * This is the only place components may trigger network requests for
 * dashboard data. Components call these functions via custom hooks.
 */

import apiClient from './apiClient';
import { BookRover } from '../types';

/**
 * Fetch the group leader performance dashboard for a bookstore.
 *
 * @param groupLeaderId - The group leader's UUID.
 * @param bookstoreId - The bookstore context UUID.
 * @param sortBy - Field to sort sellers by.
 * @param sortOrder - Sort direction.
 */
export async function fetchDashboard(
  groupLeaderId: string,
  bookstoreId: string,
  sortBy: BookRover.DashboardSortBy = 'total_amount_collected',
  sortOrder: BookRover.DashboardSortOrder = 'desc',
): Promise<BookRover.DashboardResponse> {
  const response = await apiClient.get<BookRover.DashboardResponse>(
    `/group-leaders/${groupLeaderId}/dashboard`,
    {
      params: {
        bookstore_id: bookstoreId,
        sort_by: sortBy,
        sort_order: sortOrder,
      },
    },
  );
  return response.data;
}
