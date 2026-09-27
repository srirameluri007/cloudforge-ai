import type { GenerationStatus } from "@/lib/types";

const STYLES: Record<string, string> = {
  pending: "bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200",
  running: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200",
  succeeded: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200",
  failed: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200",
};

const LABELS: Record<string, string> = {
  pending: "Pending",
  running: "Running",
  succeeded: "Succeeded",
  failed: "Failed",
};

export default function StatusBadge({ status }: { status: GenerationStatus | string }) {
  const style = STYLES[status] ?? STYLES.pending;
  const label = LABELS[status] ?? status;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
      aria-label={`Status: ${label}`}
    >
      {label}
    </span>
  );
}
