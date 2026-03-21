/**
 * ErrorBanner — dismissible red error message banner.
 *
 * Shown below the relevant section when an API call fails.
 * Auto-dismissed after 5 seconds.
 */

import { useEffect } from 'react';

interface Props {
  message: string;
  onDismiss: () => void;
}

export default function ErrorBanner({ message, onDismiss }: Props) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 5000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div
      role="alert"
      className="flex items-center justify-between rounded-lg bg-red-50 px-4 py-3 text-red-700 border border-red-200"
    >
      <span className="text-base">{message}</span>
      <button
        onClick={onDismiss}
        className="ml-4 text-red-500 hover:text-red-700 text-lg font-bold leading-none min-w-[44px] min-h-[44px] flex items-center justify-center"
        aria-label="Dismiss error"
      >
        ×
      </button>
    </div>
  );
}
