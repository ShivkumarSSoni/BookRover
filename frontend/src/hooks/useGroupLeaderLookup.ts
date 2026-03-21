/**
 * useGroupLeaderLookup — custom hook for fetching registration dropdown data.
 *
 * Fetches all group leaders with their bookstores from GET /lookup/group-leaders
 * and builds a flat list of dropdown options in the format:
 *   "Group Leader Name — Bookstore Name" → { group_leader_id, bookstore_id }
 */

import { useState, useEffect } from 'react';
import { BookRover } from '../types';
import { fetchGroupLeaderLookup } from '../services/sellerService';

interface UseGroupLeaderLookupReturn {
  options: BookRover.RegistrationDropdownOption[];
  isLoading: boolean;
  error: string | null;
}

export function useGroupLeaderLookup(): UseGroupLeaderLookupReturn {
  const [options, setOptions] = useState<BookRover.RegistrationDropdownOption[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const leaders = await fetchGroupLeaderLookup();
        if (!cancelled) {
          const flatOptions: BookRover.RegistrationDropdownOption[] = leaders.flatMap((leader) =>
            leader.bookstores.map((store) => ({
              label: `${leader.name} \u2014 ${store.store_name}`,
              group_leader_id: leader.group_leader_id,
              bookstore_id: store.bookstore_id,
            })),
          );
          setOptions(flatOptions);
        }
      } catch {
        if (!cancelled) {
          setError('Failed to load group leaders. Please try again.');
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { options, isLoading, error };
}
