/**
 * GroupLeadersTab — CRUD management for GroupLeader entities.
 *
 * Displays the list of group leaders, an add form, and inline edit/delete
 * per the Admin page spec (Tab 1: Group Leaders).
 *
 * The bookstores list is passed in as a prop so this tab re-uses the already-
 * fetched list from the parent AdminPage (avoids duplicate requests).
 */

import { useState } from 'react';
import { BookRover } from '../types';
import Spinner from '../components/Spinner';
import ErrorBanner from '../components/ErrorBanner';
import SuccessBanner from '../components/SuccessBanner';
import ConfirmDialog from '../components/ConfirmDialog';
import { useGroupLeaders } from '../hooks/useGroupLeaders';

interface Props {
  /** All bookstores — used to render the multi-select checkboxes. */
  bookstores: BookRover.BookStore[];
}

const EMPTY_ADD_FORM = { name: '', email: '', bookstore_ids: [] as string[] };

export default function GroupLeadersTab({ bookstores }: Props) {
  const {
    groupLeaders,
    isLoading,
    error,
    clearError,
    addGroupLeader,
    editGroupLeader,
    removeGroupLeader,
  } = useGroupLeaders();

  const [showAddForm, setShowAddForm] = useState(false);
  const [addForm, setAddForm] = useState(EMPTY_ADD_FORM);
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<{ name: string; bookstore_ids: string[] }>({
    name: '',
    bookstore_ids: [],
  });
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  // ── Add form ──────────────────────────────────────────────────────────────

  const isAddFormValid =
    addForm.name.trim().length > 0 &&
    addForm.email.trim().length > 0 &&
    addForm.bookstore_ids.length > 0;

  const handleAdd = async () => {
    setAddLoading(true);
    setAddError(null);
    try {
      await addGroupLeader(addForm);
      setAddForm(EMPTY_ADD_FORM);
      setShowAddForm(false);
      setSuccess('Group leader added successfully.');
    } catch (e: unknown) {
      const status = (e as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setAddError('This email is already registered.');
      } else {
        setAddError('Failed to add group leader.');
      }
    } finally {
      setAddLoading(false);
    }
  };

  const toggleAddBookstore = (id: string) => {
    setAddForm((prev) => ({
      ...prev,
      bookstore_ids: prev.bookstore_ids.includes(id)
        ? prev.bookstore_ids.filter((b) => b !== id)
        : [...prev.bookstore_ids, id],
    }));
  };

  // ── Edit form ─────────────────────────────────────────────────────────────

  const startEdit = (gl: BookRover.GroupLeader) => {
    setEditingId(gl.group_leader_id);
    setEditForm({ name: gl.name, bookstore_ids: [...gl.bookstore_ids] });
    setEditError(null);
  };

  const toggleEditBookstore = (id: string) => {
    setEditForm((prev) => ({
      ...prev,
      bookstore_ids: prev.bookstore_ids.includes(id)
        ? prev.bookstore_ids.filter((b) => b !== id)
        : [...prev.bookstore_ids, id],
    }));
  };

  const handleEditSave = async () => {
    if (!editingId) return;
    setEditLoading(true);
    setEditError(null);
    try {
      await editGroupLeader(editingId, editForm);
      setEditingId(null);
      setSuccess('Group leader updated successfully.');
    } catch {
      setEditError('Failed to update group leader.');
    } finally {
      setEditLoading(false);
    }
  };

  // ── Delete ────────────────────────────────────────────────────────────────

  const handleConfirmDelete = async () => {
    if (!deleteTargetId) return;
    try {
      await removeGroupLeader(deleteTargetId);
      setSuccess('Group leader deleted.');
    } catch (e: unknown) {
      const status = (e as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        clearError();
      }
    } finally {
      setDeleteTargetId(null);
    }
  };

  // ── Lookup helper ─────────────────────────────────────────────────────────

  const storeNameById = (id: string) =>
    bookstores.find((b) => b.bookstore_id === id)?.store_name ?? id;

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message={error} onDismiss={clearError} />}
      {success && <SuccessBanner message={success} onDismiss={() => setSuccess(null)} />}

      {/* Add form toggle */}
      {!showAddForm && (
        <button
          onClick={() => setShowAddForm(true)}
          className="w-full min-h-[44px] rounded-lg border-2 border-dashed border-indigo-300 text-indigo-600 text-base font-medium hover:border-indigo-500 hover:bg-indigo-50 transition-colors"
        >
          + Add Group Leader
        </button>
      )}

      {/* Add form */}
      {showAddForm && (
        <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-4 space-y-3">
          <h3 className="text-base font-semibold text-gray-800">New Group Leader</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              maxLength={100}
              value={addForm.name}
              onChange={(e) => setAddForm((f) => ({ ...f, name: e.target.value }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-indigo-500 focus:outline-none"
              placeholder="Ravi Kumar"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={addForm.email}
              onChange={(e) => setAddForm((f) => ({ ...f, email: e.target.value }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-indigo-500 focus:outline-none"
              placeholder="ravi@gmail.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Bookstores <span className="text-gray-400 text-xs">(select at least 1)</span>
            </label>
            {bookstores.length === 0 ? (
              <p className="text-sm text-gray-400 italic">No bookstores available. Add a bookstore first.</p>
            ) : (
              <div className="space-y-2">
                {bookstores.map((bs) => (
                  <label key={bs.bookstore_id} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={addForm.bookstore_ids.includes(bs.bookstore_id)}
                      onChange={() => toggleAddBookstore(bs.bookstore_id)}
                      className="h-5 w-5 rounded border-gray-300 text-indigo-600"
                    />
                    <span className="text-base text-gray-800">{bs.store_name}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
          {addError && <ErrorBanner message={addError} onDismiss={() => setAddError(null)} />}
          <div className="flex gap-3">
            <button
              onClick={() => { setShowAddForm(false); setAddForm(EMPTY_ADD_FORM); setAddError(null); }}
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
      {!isLoading && groupLeaders.length === 0 && (
        <p className="text-center text-gray-500 py-8">
          No group leaders yet. Add one using the button above.
        </p>
      )}
      {!isLoading &&
        groupLeaders.map((gl) =>
          editingId === gl.group_leader_id ? (
            /* Inline edit form */
            <div key={gl.group_leader_id} className="rounded-xl border border-amber-200 bg-amber-50 p-4 space-y-3">
              <h3 className="text-base font-semibold text-gray-800">Edit Group Leader</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  maxLength={100}
                  value={editForm.name}
                  onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus:border-indigo-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bookstores</label>
                <div className="space-y-2">
                  {bookstores.map((bs) => (
                    <label key={bs.bookstore_id} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={editForm.bookstore_ids.includes(bs.bookstore_id)}
                        onChange={() => toggleEditBookstore(bs.bookstore_id)}
                        className="h-5 w-5 rounded border-gray-300 text-indigo-600"
                      />
                      <span className="text-base text-gray-800">{bs.store_name}</span>
                    </label>
                  ))}
                </div>
              </div>
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
                  disabled={editLoading || editForm.bookstore_ids.length === 0}
                  className="flex-1 min-h-[44px] rounded-lg bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {editLoading ? 'Saving…' : 'Save'}
                </button>
              </div>
            </div>
          ) : (
            /* Group leader card */
            <div key={gl.group_leader_id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <div className="mb-3">
                <p className="text-base font-semibold text-gray-900">{gl.name}</p>
                <p className="text-sm text-gray-600">{gl.email}</p>
                <p className="text-sm text-gray-600 mt-1">
                  Bookstores:{' '}
                  {gl.bookstore_ids.length > 0
                    ? gl.bookstore_ids.map(storeNameById).join(', ')
                    : <span className="text-gray-400 italic">None</span>}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => startEdit(gl)}
                  className="min-h-[44px] px-4 rounded-lg border border-gray-300 text-base text-gray-700 hover:bg-gray-50"
                >
                  Edit
                </button>
                <button
                  onClick={() => setDeleteTargetId(gl.group_leader_id)}
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
          message="Delete this group leader? This cannot be undone. Deletion will fail if sellers are still assigned."
          onConfirm={handleConfirmDelete}
          onCancel={() => setDeleteTargetId(null)}
        />
      )}
    </div>
  );
}
