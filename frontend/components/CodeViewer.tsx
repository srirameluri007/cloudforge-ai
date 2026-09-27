"use client";

import Editor, { loader } from "@monaco-editor/react";
import { useEffect, useState } from "react";
import { useTheme } from "./ThemeProvider";

// Serve Monaco from the app's own /public bundle (copied at install/build
// time by scripts/copy-monaco.mjs) instead of the default jsDelivr CDN, so
// code viewing works offline and behind restrictive firewalls.
loader.config({ paths: { vs: "/monaco/vs" } });

interface CodeViewerProps {
  /** Real language label for the badge (e.g. "HCL", "Bicep"). */
  languageLabel: string;
  /** Monaco built-in language used for highlighting (see lib/constants). */
  monacoLanguage: string;
  value: string;
  fileName?: string;
  height?: string;
}

/**
 * Read-only Monaco viewer for generated code assets. If the editor fails to
 * initialize within a grace period, falls back to a plain preformatted block
 * so content is never hidden behind a spinner.
 */
export default function CodeViewer({
  languageLabel,
  monacoLanguage,
  value,
  fileName,
  height = "480px",
}: CodeViewerProps) {
  const { theme } = useTheme();
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFailed(false);
    const timer = window.setTimeout(() => setFailed(true), 20000);
    return () => window.clearTimeout(timer);
  }, [value, monacoLanguage]);

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-800">
      {(fileName || languageLabel) && (
        <div className="flex items-center justify-between bg-gray-100 px-3 py-2 dark:bg-gray-900">
          <span className="truncate font-mono text-xs text-gray-600 dark:text-gray-400">
            {fileName ?? "output"}
          </span>
          <span
            className="ml-2 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/40 dark:text-blue-200"
            aria-label={`Language: ${languageLabel}`}
          >
            {languageLabel}
          </span>
        </div>
      )}
      {failed ? (
        <pre
          className="overflow-auto p-4 font-mono text-[13px] leading-5 text-gray-900 dark:text-gray-100"
          style={{ maxHeight: height }}
          aria-label={`${fileName ?? "output"} (plain text fallback)`}
        >
          {value}
        </pre>
      ) : (
        <Editor
          height={height}
          language={monacoLanguage}
          value={value}
          theme={theme === "dark" ? "vs-dark" : "light"}
          onMount={() => setFailed(false)}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: "on",
            fontSize: 13,
            padding: { top: 12 },
            renderLineHighlight: "none",
            automaticLayout: true,
          }}
          loading={<div className="p-4 text-sm text-gray-500">Loading editor…</div>}
        />
      )}
    </div>
  );
}
