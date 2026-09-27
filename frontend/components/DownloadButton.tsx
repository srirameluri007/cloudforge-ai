"use client";

import { useState } from "react";
import { downloadFile, saveBlob } from "@/lib/api";

interface DownloadButtonProps {
  /** API path, e.g. `/api/v1/assets/123/download`. */
  href: string;
  /** Fallback filename if the server omits Content-Disposition. */
  fallbackFilename: string;
  label?: string;
}

/** Downloads a generated asset through the backend and saves it locally. */
export default function DownloadButton({
  href,
  fallbackFilename,
  label = "Download",
}: DownloadButtonProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDownload() {
    setBusy(true);
    setError(null);
    try {
      const { blob, filename } = await downloadFile(href);
      saveBlob(blob, filename || fallbackFilename);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className="inline-flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={handleDownload}
        disabled={busy}
        className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
      >
        {busy ? "Downloading…" : label}
      </button>
      {error && (
        <span role="alert" className="text-xs text-red-600 dark:text-red-400">
          {error}
        </span>
      )}
    </span>
  );
}
