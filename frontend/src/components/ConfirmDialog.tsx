/**
 * ConfirmDialog — modal confirmation dialog for destructive actions.
 *
 * Shown before delete operations. Contains "Confirm" and "Cancel" buttons.
 */

interface Props {
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({ message, onConfirm, onCancel }: Props) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
        <p className="mb-6 text-base text-gray-800">{message}</p>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 min-h-[44px] rounded-lg border border-gray-300 bg-white text-base text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 min-h-[44px] rounded-lg bg-red-600 text-base font-medium text-white hover:bg-red-700"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}
