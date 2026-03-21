/**
 * useGroupLeaders — custom hook for GroupLeader CRUD state.
 *
 * Manages all GroupLeader data fetching and mutation. Components are pure
 * presentation — they call functions from this hook, never apiClient directly.
 */

import { useState, useEffect, useCallback } from 'react';
import { BookRover } from '../types';
import {
  fetchGroupLeaders,
  createGroupLeader,
  updateGroupLeader,
  deleteGroupLeader,
} from '../services/adminService';

interface UseGroupLeadersReturn {
  groupLeaders: BookRover.GroupLeader[];
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
  addGroupLeader: (payload: BookRover.GroupLeaderCreate) => Promise<void>;
  editGroupLeader: (id: string, payload: BookRover.GroupLeaderUpdate) => Promise<void>;
  removeGroupLeader: (id: string) => Promise<void>;
  refresh: () => void;
}

export function useGroupLeaders(): UseGroupLeadersReturn {
  const [groupLeaders, setGroupLeaders] = useState<BookRover.GroupLeader[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchGroupLeaders();
      setGroupLeaders(data);
    } catch {
      setError('Failed to load group leaders. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const addGroupLeader = async (payload: BookRover.GroupLeaderCreate) => {
    const created = await createGroupLeader(payload);
    setGroupLeaders((prev) => [...prev, created]);
  };

  const editGroupLeader = async (id: string, payload: BookRover.GroupLeaderUpdate) => {
    const updated = await updateGroupLeader(id, payload);
    setGroupLeaders((prev) => prev.map((g) => (g.group_leader_id === id ? updated : g)));
  };

  const removeGroupLeader = async (id: string) => {
    await deleteGroupLeader(id);
    setGroupLeaders((prev) => prev.filter((g) => g.group_leader_id !== id));
  };

  return {
    groupLeaders,
    isLoading,
    error,
    clearError: () => setError(null),
    addGroupLeader,
    editGroupLeader,
    removeGroupLeader,
    refresh: load,
  };
}
