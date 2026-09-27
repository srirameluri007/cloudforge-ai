export default function ErrorBanner({
  message,
  onDismiss,
  title = "Something went wrong",
}: {
  message: string;
  onDismiss?: () => void;
  title?: string;
}) {
  return (
    <div
      role="alert"
      className="rounded-md border border-red-300 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950/40"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-red-800 dark:text-red-200">{title}</p>
          <p className="mt-1 text-sm text-red-700 dark:text-red-300">{message}</p>
        </div>
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            aria-label="Dismiss error"
            className="rounded p-1 text-red-600 hover:bg-red-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-500 dark:text-red-300 dark:hover:bg-red-900/50"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
