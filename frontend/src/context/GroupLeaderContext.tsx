/**
 * GroupLeaderContext — React context that holds the current group leader's identity.
 *
 * Reads `bookrover_group_leader_id` from localStorage. The group leader's
 * name and other profile data are obtained via the dashboard response itself —
 * no separate profile fetch is needed.
 *
 * Usage:
 *   - Wrap group leader routes in <GroupLeaderProvider> inside App.tsx.
 *   - Read group_leader_id in any component via useGroupLeader().
 */

import { createContext, useContext, ReactNode } from 'react';

// ─── Context shape ─────────────────────────────────────────────────────────────

interface GroupLeaderContextValue {
  groupLeaderId: string | null;
}

const GroupLeaderContext = createContext<GroupLeaderContextValue | null>(null);

// ─── Provider ───────────────────────────────────────────────────────────────────

interface GroupLeaderProviderProps {
  children: ReactNode;
}

export function GroupLeaderProvider({ children }: GroupLeaderProviderProps) {
  const groupLeaderId = localStorage.getItem('bookrover_group_leader_id');

  return (
    <GroupLeaderContext.Provider value={{ groupLeaderId }}>
      {children}
    </GroupLeaderContext.Provider>
  );
}

// ─── Hook ───────────────────────────────────────────────────────────────────────

export function useGroupLeader(): GroupLeaderContextValue {
  const ctx = useContext(GroupLeaderContext);
  if (!ctx) {
    throw new Error('useGroupLeader must be used inside <GroupLeaderProvider>');
  }
  return ctx;
}
