/**
 * AdminPage — CRUD management for Group Leaders and Bookstores.
 *
 * Route: /admin
 * Access: Admin only.
 *
 * Layout: Two tabs — "Group Leaders" (Tab 1) and "Bookstores" (Tab 2).
 * Bookstores are fetched here and passed to GroupLeadersTab so checkbox
 * rendering does not require a second fetch.
 */

import { useState } from 'react';
import GroupLeadersTab from './GroupLeadersTab';
import BookstoresTab from './BookstoresTab';
import { useBookstores } from '../hooks/useBookstores';

type Tab = 'group-leaders' | 'bookstores';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>('group-leaders');

  // Single useBookstores instance — shared with both BookstoresTab (mutations)
  // and GroupLeadersTab (read-only list for checkbox rendering).
  // This ensures GroupLeadersTab always sees bookstores added in BookstoresTab.
  const { bookstores, isLoading: bookstoresLoading, error: bookstoresError, clearError: clearBookstoresError, addBookstore, editBookstore, removeBookstore } = useBookstores();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <h1 className="text-xl font-brand font-semibold text-blue-600">BookRover Admin</h1>
        <p className="text-sm text-gray-500">Manage group leaders and bookstores</p>
      </header>

      {/* Tab bar */}
      <div className="bg-white border-b border-gray-200 px-4">
        <nav className="flex" aria-label="Admin tabs">
          <button
            onClick={() => setActiveTab('group-leaders')}
            className={[
              'flex-1 py-3 text-base font-medium border-b-2 transition-colors',
              activeTab === 'group-leaders'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700',
            ].join(' ')}
            aria-selected={activeTab === 'group-leaders'}
          >
            Group Leaders
          </button>
          <button
            onClick={() => setActiveTab('bookstores')}
            className={[
              'flex-1 py-3 text-base font-medium border-b-2 transition-colors',
              activeTab === 'bookstores'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700',
            ].join(' ')}
            aria-selected={activeTab === 'bookstores'}
          >
            Bookstores
          </button>
        </nav>
      </div>

      {/* Tab content */}
      <main className="max-w-lg mx-auto px-4 py-6">
        {activeTab === 'group-leaders' ? (
          <GroupLeadersTab bookstores={bookstores} />
        ) : (
          <BookstoresTab
            bookstores={bookstores}
            isLoading={bookstoresLoading}
            error={bookstoresError}
            clearError={clearBookstoresError}
            addBookstore={addBookstore}
            editBookstore={editBookstore}
            removeBookstore={removeBookstore}
          />
        )}
      </main>
    </div>
  );
}
