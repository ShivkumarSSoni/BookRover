/**
 * BookstoresTab — CRUD management for BookStore entities.
 *
 * Displays the list of bookstores, an add form, and inline edit/delete
 * per the Admin page spec (Tab 2: Bookstores).
 */

import { useState } from 'react';
import { BookRover } from '../types';
import Spinner from '../components/Spinner';
import ErrorBanner from '../components/ErrorBanner';
import SuccessBanner from '../components/SuccessBanner';
import ConfirmDialog from '../components/ConfirmDialog';
import { useBookstores } from '../hooks/useBookstores';

const EMPTY_FORM: BookRover.BookStoreCreate = {
  store_name: '',
  owner_name: '',
  address: '',
  phone_number: '',
};

export default function BookstoresTab() {
  const { bookstores, isLoading, error, clearError, addBookstore, editBookstore, removeBookstore } =
    useBookstores();

  const [showAddForm, setShowAddForm] = useState(false);
  const [addForm, setAddForm] = useState<BookRover.BookStoreCreate>(EMPTY_FORM);
  const [addError, setAddError] = useState<string | null>(null);
  const [addLoading, setAddLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<BookRover.BookStoreCreate>(EMPTY_FORM);
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  // ── Add form ──────────────────────────────────────────────────────────────

  const isAddFormValid = Object.values(addForm).every((v) => v.trim().length > 0);

  const handleAdd = async () => {
    setAddLoading(true);
    setAddError(null);
    try {
      await addBookstore(addForm);
      setAddForm(EMPTY_FORM);
      setShowAddForm(false);
      setSuccess('Bookstore added successfully.');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to add bookstore.';
      setAddError(msg);
    } finally {
      setAddLoading(false);
    }
  };

  // ── Edit form ─────────────────────────────────────────────────────────────

  const startEdit = (bookstore: BookRover.BookStore) => {
    setEditingId(bookstore.bookstore_id);
    setEditForm({
      store_name: bookstore.store_name,
      owner_name: bookstore.owner_name,
      address: bookstore.address,
      phone_number: bookstore.phone_number,
    });
    setEditError(null);
  };

  const handleEditSave = async () => {
    if (!editingId) return;
    setEditLoading(true);
    setEditError(null);
    try {
      await editBookstore(editingId, editForm);
      setEditingId(null);
      setSuccess('Bookstore updated successfully.');
    } catch {
      setEditError('Failed to update bookstore.');
    } finally {
      setEditLoading(false);
    }
  };

  // ── Delete ────────────────────────────────────────────────────────────────

  const handleConfirmDelete = async () => {
    if (!deleteTargetId) return;
    try {
      await removeBookstore(deleteTargetId);
      setSuccess('Bookstore deleted.');
    } catch {
      // error will be surfaced via the hook's error state
    } finally {
      setDeleteTargetId(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Global error from hook (load failures) */}
      {error && <ErrorBanner message={error} onDismiss={clearError} />}
      {success && <SuccessBanner message={success} onDismiss={() => setSuccess(null)} />}

      {/* Add form toggle */}
      {!showAddForm && (
        <button
          onClick={() => setShowAddForm(true)}
          className="w-full min-h-[44px] rounded-lg border-2 border-dashed border-indigo-300 text-indigo-600 text-base font-medium hover:border-indigo-500 hover:bg-indigo-50 transition-colors"
        >
          + Add Bookstore
        </button>
      )}

      {/* Add form */}
      {showAddForm && (
        <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-4 space-y-3">
          <h3 className="text-base font-semibold text-gray-800">New Bookstore</h3>
          <BookstoreFormFields form={addForm} onChange={setAddForm} />
          {addError && <ErrorBanner message={addError} onDismiss={() => setAddError(null)} />}
          <div className="flex gap-3">
            <button
              onClick={() => { setShowAddForm(false); setAddForm(EMPTY_FORM); setAddError(null); }}
              className="flex-1 min-h-[44px] rounded-lg border border-gray-300 bg-white text-base text-gray-700 hover:bg-gray-50"
              disabled={addLoading}
            >
              Cancel
            </button>
            <button
              onClick={handleAdd}
              disabled={!isAddFormValid || addLoading}
              className="flex-1 min-h-[44px] rounded-lg bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {addLoading ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      )}

      {/* List */}
      {isLoading && <Spinner />}
      {!isLoading && bookstores.length === 0 && (
        <p className="text-center text-gray-500 py-8">
          No bookstores yet. Add one using the button above.
        </p>
      )}
      {!isLoading &&
        bookstores.map((bs) =>
          editingId === bs.bookstore_id ? (
            /* Inline edit form */
            <div key={bs.bookstore_id} className="rounded-xl border border-amber-200 bg-amber-50 p-4 space-y-3">
              <h3 className="text-base font-semibold text-gray-800">Edit Bookstore</h3>
              <BookstoreFormFields form={editForm} onChange={setEditForm} />
              {editError && <ErrorBanner message={editError} onDismiss={() => setEditError(null)} />}
              <div className="flex gap-3">
                <button
                  onClick={() => setEditingId(null)}
                  className="flex-1 min-h-[44px] rounded-lg border border-gray-300 bg-white text-base text-gray-700 hover:bg-gray-50"
                  disabled={editLoading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleEditSave}
                  disabled={editLoading}
                  className="flex-1 min-h-[44px] rounded-lg bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {editLoading ? 'Saving…' : 'Save'}
                </button>
              </div>
            </div>
          ) : (
            /* Bookstore card */
            <div key={bs.bookstore_id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <div className="mb-3">
                <p className="text-base font-semibold text-gray-900">{bs.store_name}</p>
                <p className="text-sm text-gray-600">Owner: {bs.owner_name}</p>
                <p className="text-sm text-gray-600">Address: {bs.address}</p>
                <p className="text-sm text-gray-600">Phone: {bs.phone_number}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => startEdit(bs)}
                  className="min-h-[44px] px-4 rounded-lg border border-gray-300 text-base text-gray-700 hover:bg-gray-50"
                >
                  Edit
                </button>
                <button
                  onClick={() => setDeleteTargetId(bs.bookstore_id)}
                  className="min-h-[44px] px-4 rounded-lg border border-red-200 text-base text-red-600 hover:bg-red-50"
                >
                  Delete
                </button>
              </div>
            </div>
          ),
        )}

      {/* Delete confirm dialog */}
      {deleteTargetId && (
        <ConfirmDialog
          message="Delete this bookstore? This action cannot be undone."
          onConfirm={handleConfirmDelete}
          onCancel={() => setDeleteTargetId(null)}
        />
      )}
    </div>
  );
}

// ── Shared form fields component ──────────────────────────────────────────────

interface FormFieldsProps {
  form: BookRover.BookStoreCreate;
  onChange: (form: BookRover.BookStoreCreate) => void;
}

function BookstoreFormFields({ form, onChange }: FormFieldsProps) {
  const update = (field: keyof BookRover.BookStoreCreate, value: string) =>
    onChange({ ...form, [field]: value });

  return (
    <>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Store Name</label>
        <input
          type="text"
          maxLength={100}
          value={form.store_name}
          onChange={(e) => update('store_name', e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-indigo-500 focus:outline-none"
          placeholder="Sri Lakshmi Books"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Owner Name</label>
        <input
          type="text"
          maxLength={100}
          value={form.owner_name}
          onChange={(e) => update('owner_name', e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-indigo-500 focus:outline-none"
          placeholder="Lakshmi Devi"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
        <textarea
          maxLength={500}
          value={form.address}
          onChange={(e) => update('address', e.target.value)}
          rows={2}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-indigo-500 focus:outline-none resize-none"
          placeholder="12 MG Road, Chennai, TN 600001"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
        <input
          type="text"
          maxLength={20}
          value={form.phone_number}
          onChange={(e) => update('phone_number', e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-indigo-500 focus:outline-none"
          placeholder="+914423456789"
        />
      </div>
    </>
  );
}
