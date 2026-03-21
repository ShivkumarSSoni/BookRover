/**
 * SuccessBanner — auto-dismissing green success message banner.
 *
 * Auto-dismissed after 3 seconds per the global UI spec.
 */

import { useEffect } from 'react';

interface Props {
  message: string;
  onDismiss: () => void;
}

export default function SuccessBanner({ message, onDismiss }: Props) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 3000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div
      role="status"
      className="flex items-center justify-between rounded-lg bg-green-50 px-4 py-3 text-green-700 border border-green-200"
    >
      <span className="text-base">{message}</span>
      <button
        onClick={onDismiss}
        className="ml-4 text-green-500 hover:text-green-700 text-lg font-bold leading-none min-w-[44px] min-h-[44px] flex items-center justify-center"
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  );
}
