/**
 * BookRover TypeScript namespace — Admin domain types.
 *
 * All interfaces for BookStore and GroupLeader entities used by the Admin feature.
 * Components and services import from `src/types/index.ts`.
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
}
