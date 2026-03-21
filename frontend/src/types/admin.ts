/**
 * BookRover TypeScript namespace — Admin and Seller domain types.
 *
 * All interfaces for BookStore, GroupLeader, Seller entities and Lookup
 * responses. Components and services import from `src/types/index.ts`.
 */

export namespace BookRover {
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
}
