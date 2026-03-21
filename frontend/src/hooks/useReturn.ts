/**
 * useReturn — custom hook for the Seller Return Books feature.
 *
 * Fetches the return summary on mount and exposes submitReturn to record
 * the return. After a successful submission the summary is cleared so the
 * page can render the success state.
 */

import { useState, useEffect, useCallback } from 'react';
import { BookRover } from '../types';
import {
  fetchReturnSummary,
  submitReturn as apiSubmitReturn,
} from '../services/returnService';

interface UseReturnReturn {
  summary: BookRover.ReturnSummaryResponse | null;
  isLoading: boolean;
  error: string | null;
  isSubmitting: boolean;
  submitSuccess: boolean;
  submitReturn: (notes?: string) => Promise<void>;
  submitError: string | null;
}

export function useReturn(sellerId: string): UseReturnReturn {
  const [summary, setSummary] = useState<BookRover.ReturnSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!sellerId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchReturnSummary(sellerId);
      setSummary(data);
    } catch {
      setError('Failed to load return summary. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [sellerId]);

  useEffect(() => {
    load();
  }, [load]);

  const submitReturn = async (notes?: string) => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await apiSubmitReturn(sellerId, notes);
      setSubmitSuccess(true);
    } catch {
      setSubmitError('Failed to submit return. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    summary,
    isLoading,
    error,
    isSubmitting,
    submitSuccess,
    submitReturn,
    submitError,
  };
}
