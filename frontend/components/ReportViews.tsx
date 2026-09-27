"use client";

import type { AssetSummary } from "@/lib/types";
import { SEVERITY_ORDER, tabDefinitionFor } from "@/lib/constants";
import CodeViewer from "./CodeViewer";
import CopyButton from "./CopyButton";
import DownloadButton from "./DownloadButton";
import Spinner from "./Spinner";

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

export function tryParseJson(content: string): unknown | null {
  try {
    return JSON.parse(content);
  } catch {
    return null;
  }
}

export function RawReportFallback({
  summary,
  content,
}: {
  summary: AssetSummary;
  content: string;
}) {
  const def = tabDefinitionFor(summary.asset_type);
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <CopyButton text={content} />
        <DownloadButton
          href={`/api/v1/assets/${summary.id}/download`}
          fallbackFilename={summary.file_name}
        />
      </div>
      <CodeViewer
        languageLabel={def.languageLabel}
        monacoLanguage="markdown"
        value={content}
        fileName={summary.file_name}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Security tab
// ---------------------------------------------------------------------------

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-600 text-white",
  high: "bg-orange-500 text-white",
  medium: "bg-amber-400 text-black",
  low: "bg-blue-500 text-white",
  info: "bg-gray-500 text-white",
};

interface SeverityFinding {
  severity?: string;
  title: string;
  description?: string;
}

export function SecurityReportView({
  summary,
  content,
}: {
  summary: AssetSummary;
  content: string;
}) {
  const parsed = tryParseJson(content) as { findings?: SeverityFinding[] } | null;
  const findings = Array.isArray(parsed?.findings) ? parsed.findings : null;

  if (!findings) {
    return <RawReportFallback summary={summary} content={content} />;
  }

  const grouped = SEVERITY_ORDER.map((sev) => ({
    severity: sev,
    items: findings.filter((f) => (f.severity ?? "info") === sev),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Automated guidance, not a formal security audit.
      </p>
      {grouped.length === 0 && (
        <p className="text-sm text-gray-600 dark:text-gray-400">
          No findings reported for this generation.
        </p>
      )}
      {grouped.map((group) => (
        <section key={group.severity} aria-label={`${group.severity} severity findings`}>
          <h3 className="mb-2 text-sm font-semibold capitalize text-gray-700 dark:text-gray-300">
            {group.severity} ({group.items.length})
          </h3>
          <ul className="space-y-2">
            {group.items.map((finding, i) => (
              <li
                key={`${finding.title}-${i}`}
                className="rounded-md border border-gray-200 p-3 dark:border-gray-800"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase ${SEVERITY_STYLES[group.severity]}`}
                  >
                    {group.severity}
                  </span>
                  <span className="text-sm font-medium">{finding.title}</span>
                </div>
                {finding.description && (
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {finding.description}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Zero Trust tab
// ---------------------------------------------------------------------------

export function ScoreBar({ label, value }: { label: string; value: number }) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  const color =
    clamped >= 80 ? "bg-green-500" : clamped >= 50 ? "bg-amber-400" : "bg-red-500";
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="font-medium capitalize">{label}</span>
        <span className="text-gray-600 dark:text-gray-400">{clamped}/100</span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label} score`}
        className="h-2.5 w-full rounded-full bg-gray-200 dark:bg-gray-700"
      >
        <div className={`h-2.5 rounded-full ${color}`} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}

interface ZeroTrustScoreData {
  identity: number;
  network: number;
  data: number;
  workload: number;
  overall: number;
  recommendations?: string[];
}

export function ZeroTrustView({
  summary,
  content,
}: {
  summary: AssetSummary;
  content: string;
}) {
  const parsed = tryParseJson(content) as ZeroTrustScoreData | null;
  const hasScores =
    parsed !== null &&
    ["identity", "network", "data", "workload", "overall"].every(
      (k) => typeof (parsed as unknown as Record<string, unknown>)[k] === "number",
    );

  if (!hasScores) {
    return <RawReportFallback summary={summary} content={content} />;
  }

  const scores = parsed as ZeroTrustScoreData;
  const recommendations = Array.isArray(scores.recommendations) ? scores.recommendations : [];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <ScoreBar label="Identity" value={scores.identity} />
        <ScoreBar label="Network" value={scores.network} />
        <ScoreBar label="Data" value={scores.data} />
        <ScoreBar label="Workload" value={scores.workload} />
        <ScoreBar label="Overall" value={scores.overall} />
      </div>
      {recommendations.length > 0 && (
        <section aria-label="Zero trust recommendations">
          <h3 className="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            Recommendations
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-gray-600 dark:text-gray-400">
            {recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Cost tab
// ---------------------------------------------------------------------------

interface CostReport {
  drivers?: string[];
  optimizations?: string[];
  disclaimer?: string;
}

export function CostDisclaimer({ custom }: { custom?: string }) {
  return (
    <p className="rounded-md border border-gray-200 bg-gray-50 p-3 text-xs text-gray-600 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400">
      {custom ??
        "Estimates are indicative only and based on list pricing at generation time. Actual costs depend on usage, region, and discounts — validate with your cloud provider's pricing calculator."}
    </p>
  );
}

export function CostView({
  summary,
  content,
}: {
  summary: AssetSummary;
  content: string;
}) {
  const parsed = tryParseJson(content) as CostReport | null;
  const hasStructured =
    parsed !== null &&
    (Array.isArray(parsed.drivers) || Array.isArray(parsed.optimizations));

  if (!hasStructured) {
    return (
      <div className="space-y-3">
        <CostDisclaimer />
        <RawReportFallback summary={summary} content={content} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <CostDisclaimer custom={parsed?.disclaimer} />
      {parsed?.drivers && parsed.drivers.length > 0 && (
        <section aria-label="Cost drivers">
          <h3 className="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            Cost drivers
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-gray-600 dark:text-gray-400">
            {parsed.drivers.map((d, i) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
        </section>
      )}
      {parsed?.optimizations && parsed.optimizations.length > 0 && (
        <section aria-label="Cost optimizations">
          <h3 className="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            Optimizations
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-gray-600 dark:text-gray-400">
            {parsed.optimizations.map((o, i) => (
              <li key={i}>{o}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Code asset tab (used by tests as well)
// ---------------------------------------------------------------------------

export function CodeAssetView({
  summary,
  content,
}: {
  summary: AssetSummary;
  content: string;
}) {
  const def = tabDefinitionFor(summary.asset_type);
  if (!content) {
    return <Spinner label="Loading asset…" />;
  }
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <CopyButton text={content} />
        <DownloadButton
          href={`/api/v1/assets/${summary.id}/download`}
          fallbackFilename={summary.file_name}
        />
      </div>
      <CodeViewer
        languageLabel={def.languageLabel}
        monacoLanguage={def.monacoLanguage}
        value={content}
        fileName={summary.file_name}
      />
    </div>
  );
}
