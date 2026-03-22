/**
 * BookRover TypeScript namespace — Admin and Seller domain types.
 *
 * All interfaces for BookStore, GroupLeader, Seller entities and Lookup
 * responses. Components and services import from `src/types/index.ts`.
 */

export namespace BookRover {
  // ── Auth types ────────────────────────────────────────────────────────────

  export type Role = 'admin' | 'group_leader' | 'seller';

  /** Response from GET /me — the caller's identity and resolved BookRover roles. */
  export interface MeResponse {
    email: string;
    roles: Role[];
    seller_id: string | null;
    group_leader_id: string | null;
  }

  /** Response from POST /dev/mock-token — dev-only. */
  export interface MockTokenResponse {
    token: string;
    email: string;
  }

  // ── Admin types ───────────────────────────────────────────────────────────

  export interface BookStore {
    bookstore_id: string;
    store_name: string;
    owner_name: string;
    address: string;
    phone_number: string;
    created_at: string;
    updated_at: string;
  }

  export interface BookStoreCreate {
    store_name: string;
    owner_name: string;
    address: string;
    phone_number: string;
  }

  export interface BookStoreUpdate {
    store_name?: string;
    owner_name?: string;
    address?: string;
    phone_number?: string;
  }

  export interface GroupLeader {
    group_leader_id: string;
    name: string;
    email: string;
    bookstore_ids: string[];
    created_at: string;
    updated_at: string;
  }

  export interface GroupLeaderCreate {
    name: string;
    email: string;
    bookstore_ids: string[];
  }

  export interface GroupLeaderUpdate {
    name?: string;
    bookstore_ids?: string[];
  }

  // ── Seller types ──────────────────────────────────────────────────────────

  export interface Seller {
    seller_id: string;
    first_name: string;
    last_name: string;
    email: string;
    group_leader_id: string;
    bookstore_id: string;
    status: string;
    created_at: string;
    updated_at: string;
  }

  export interface SellerCreate {
    first_name: string;
    last_name: string;
    email: string;
    group_leader_id: string;
    bookstore_id: string;
  }

  export interface BookStoreSummary {
    bookstore_id: string;
    store_name: string;
  }

  export interface GroupLeaderLookup {
    group_leader_id: string;
    name: string;
    bookstores: BookStoreSummary[];
  }

  /** A single option in the registration dropdown. */
  export interface RegistrationDropdownOption {
    label: string;
    group_leader_id: string;
    bookstore_id: string;
  }

  // ── Inventory types ───────────────────────────────────────────────────────

  export interface Book {
    book_id: string;
    seller_id: string;
    bookstore_id: string;
    book_name: string;
    language: string;
    initial_count: number;
    current_count: number;
    cost_per_book: number;
    selling_price: number;
    current_books_cost_balance: number;
    total_books_cost_balance: number;
    created_at: string;
    updated_at: string;
  }

  export interface BookCreate {
    book_name: string;
    language: string;
    initial_count: number;
    cost_per_book: number;
    selling_price: number;
  }

  export interface BookUpdate {
    book_name?: string;
    language?: string;
    cost_per_book?: number;
    selling_price?: number;
  }

  export interface InventorySummary {
    total_books_in_hand: number;
    total_cost_balance: number;
    total_initial_cost: number;
  }

  export interface InventoryResponse {
    seller_id: string;
    bookstore_id: string;
    books: Book[];
    summary: InventorySummary;
  }

  // ── Sale types ────────────────────────────────────────────────────────────

  export interface SaleItemCreate {
    book_id: string;
    quantity_sold: number;
  }

  export interface SaleCreate {
    buyer_first_name: string;
    buyer_last_name: string;
    buyer_country_code: string;
    buyer_phone: string;
    items: SaleItemCreate[];
  }

  export interface SaleItemResponse {
    book_id: string;
    book_name: string;
    language: string;
    quantity_sold: number;
    selling_price: number;
    subtotal: number;
  }

  export interface SaleResponse {
    sale_id: string;
    seller_id: string;
    bookstore_id: string;
    buyer_first_name: string;
    buyer_last_name: string;
    buyer_country_code: string;
    buyer_phone: string;
    sale_items: SaleItemResponse[];
    total_books_sold: number;
    total_amount_collected: number;
    sale_date: string;
    created_at: string;
  }

  // ── Dashboard types ───────────────────────────────────────────────────────

  export interface DashboardGroupLeader {
    group_leader_id: string;
    name: string;
  }

  export interface DashboardBookstore {
    bookstore_id: string;
    store_name: string;
  }

  export interface DashboardSellerRow {
    seller_id: string;
    full_name: string;
    total_books_sold: number;
    total_amount_collected: number;
  }

  export interface DashboardTotals {
    total_books_sold: number;
    total_amount_collected: number;
  }

  export interface DashboardResponse {
    group_leader: DashboardGroupLeader;
    bookstore: DashboardBookstore;
    sellers: DashboardSellerRow[];
    totals: DashboardTotals;
  }

  export type DashboardSortBy = 'total_books_sold' | 'total_amount_collected';
  export type DashboardSortOrder = 'asc' | 'desc';

  // ── Return types ──────────────────────────────────────────────────────────

  export interface ReturnSummaryBookstoreInfo {
    bookstore_id: string;
    store_name: string;
    owner_name: string;
    address: string;
    phone_number: string;
  }

  export interface ReturnSummaryBook {
    book_id: string;
    book_name: string;
    language: string;
    quantity_to_return: number;
    cost_per_book: number;
    total_cost: number;
  }

  export interface ReturnSummaryResponse {
    seller_id: string;
    bookstore: ReturnSummaryBookstoreInfo;
    books_to_return: ReturnSummaryBook[];
    total_books_to_return: number;
    total_cost_of_unsold_books: number;
    total_money_collected_from_sales: number;
  }

  export interface ReturnItemResponse {
    book_id: string;
    book_name: string;
    language: string;
    quantity_returned: number;
    cost_per_book: number;
    total_cost: number;
  }

  export interface ReturnResponse {
    return_id: string;
    seller_id: string;
    bookstore_id: string;
    return_items: ReturnItemResponse[];
    total_books_returned: number;
    total_money_returned: number;
    status: string;
    return_date: string;
  }
}
