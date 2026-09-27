"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ApiError, downloadFile, get, patch, post, saveBlob } from "@/lib/api";
import type {
  AiProviderSettings,
  Asset,
  AssetListResponse,
  AssetSummary,
  AssetType,
  Generation,
  GenerationListResponse,
  GenerationStatus,
  Project,
} from "@/lib/types";
import {
  AVAILABILITY_OPTIONS,
  CLOUD_TARGET_OPTIONS,
  COMPLIANCE_OPTIONS,
  ENVIRONMENT_OPTIONS,
  PROMPT_MIN_LENGTH,
  TAB_DEFINITIONS,
  tabDefinitionFor,
} from "@/lib/constants";
import {
  CostView,
  SecurityReportView,
  ZeroTrustView,
} from "@/components/ReportViews";
import Tabs from "@/components/Tabs";
import CodeViewer from "@/components/CodeViewer";
import CopyButton from "@/components/CopyButton";
import DownloadButton from "@/components/DownloadButton";
import EmptyState from "@/components/EmptyState";
import ErrorBanner from "@/components/ErrorBanner";
import Spinner from "@/components/Spinner";
import StatusBadge from "@/components/StatusBadge";
import DemoBanner from "@/components/DemoBanner";
import { SkeletonCard } from "@/components/Skeleton";

const inputClass =
  "w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100";

const TERMINAL_STATUSES: GenerationStatus[] = ["succeeded", "failed"];

// ---------------------------------------------------------------------------

export default function ProjectStudioPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);

  const [generations, setGenerations] = useState<Generation[]>([]);
  const [activeGeneration, setActiveGeneration] = useState<Generation | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [promptError, setPromptError] = useState<string | null>(null);

  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [assetsLoading, setAssetsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("terraform");
  const [assetContents, setAssetContents] = useState<Record<string, string>>({});
  const [assetLoadingId, setAssetLoadingId] = useState<string | null>(null);
  const [assetError, setAssetError] = useState<string | null>(null);

  const [aiSettings, setAiSettings] = useState<AiProviderSettings | null>(null);
  const [exportBusy, setExportBusy] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const showDemoBanner =
    aiSettings?.demo_mode === true || activeGeneration?.provider === "demo";

  // -- initial load ---------------------------------------------------------
  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setPageError(null);
      try {
        const [proj, gens] = await Promise.all([
          get<Project>(`/api/v1/projects/${projectId}`),
          get<GenerationListResponse>(`/api/v1/projects/${projectId}/generations`),
        ]);
        if (cancelled) return;
        setProject(proj);
        const items = gens.items ?? [];
        setGenerations(items);
        const latest = items[0] ?? null;
        setActiveGeneration(latest);
        if (proj.original_prompt) setPrompt(proj.original_prompt);
      } catch (err) {
        if (!cancelled) {
          setPageError(err instanceof ApiError ? err.message : "Could not load the project.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  // -- AI provider settings (for demo banner) --------------------------------
  useEffect(() => {
    let cancelled = false;
    get<AiProviderSettings>("/api/v1/settings/ai-provider")
      .then((s) => {
        if (!cancelled) setAiSettings(s);
      })
      .catch(() => {
        /* non-fatal: banner simply stays hidden */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // -- poll a running generation until it reaches a terminal state ------------
  useEffect(() => {
    const gen = activeGeneration;
    if (!gen || TERMINAL_STATUSES.includes(gen.status)) return;
    const genId = gen.id;
    let cancelled = false;
    const timer = window.setInterval(async () => {
      try {
        const updated = await get<Generation>(`/api/v1/generations/${genId}`);
        if (cancelled) return;
        setActiveGeneration(updated);
        setGenerations((prev) => prev.map((g) => (g.id === updated.id ? updated : g)));
      } catch {
        /* keep polling; a later tick may succeed */
      }
    }, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
    // Depend on the primitive id/status only: re-polling on every object
    // identity change (from setGenerations updates) would reset the timer.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeGeneration?.id, activeGeneration?.status]);

  // -- load asset summaries when the active generation changes ----------------
  useEffect(() => {
    const gen = activeGeneration;
    if (!gen) {
      setAssets([]);
      return;
    }
    const genId = gen.id;
    let cancelled = false;
    async function loadAssets() {
      setAssetsLoading(true);
      try {
        const res = await get<AssetListResponse>(`/api/v1/generations/${genId}/assets`);
        if (!cancelled) setAssets(res.items ?? []);
      } catch {
        if (!cancelled) setAssets([]);
      } finally {
        if (!cancelled) setAssetsLoading(false);
      }
    }
    void loadAssets();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeGeneration?.id]);

  const assetByType = useCallback(
    (type: AssetType): AssetSummary | undefined => assets.find((a) => a.asset_type === type),
    [assets],
  );

  // -- lazily fetch asset content when its tab is selected -------------------
  useEffect(() => {
    const summary = assetByType(activeTab as AssetType);
    if (!summary || assetContents[summary.id]) return;
    let cancelled = false;
    setAssetLoadingId(summary.id);
    setAssetError(null);
    get<Asset>(`/api/v1/assets/${summary.id}`)
      .then((asset) => {
        if (cancelled) return;
        setAssetContents((prev) => ({ ...prev, [summary.id]: asset.content }));
      })
      .catch((err) => {
        if (cancelled) return;
        setAssetError(err instanceof ApiError ? err.message : "Could not load the asset.");
      })
      .finally(() => {
        if (!cancelled) setAssetLoadingId(null);
      });
    return () => {
      cancelled = true;
    };
  }, [activeTab, assetByType, assetContents]);

  // -- actions ----------------------------------------------------------------
  async function handleGenerate() {
    setGenerateError(null);
    setPromptError(null);
    const trimmed = prompt.trim();
    if (trimmed.length < PROMPT_MIN_LENGTH) {
      setPromptError(
        `Describe your infrastructure in at least ${PROMPT_MIN_LENGTH} characters so the generator has enough detail.`,
      );
      return;
    }
    setGenerating(true);
    try {
      const gen = await post<Generation>(`/api/v1/projects/${projectId}/generate`, {
        prompt: trimmed,
      });
      setGenerations((prev) => [gen, ...prev]);
      setActiveGeneration(gen);
      setAssets([]);
      setAssetContents({});
      setActiveTab("terraform");
    } catch (err) {
      setGenerateError(err instanceof ApiError ? err.message : "Generation failed to start.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleRetry() {
    const gen = activeGeneration;
    if (!gen) return;
    setGenerateError(null);
    setGenerating(true);
    try {
      const fresh = await post<Generation>(`/api/v1/generations/${gen.id}/retry`);
      setGenerations((prev) => [fresh, ...prev]);
      setActiveGeneration(fresh);
      setAssets([]);
      setAssetContents({});
    } catch (err) {
      setGenerateError(err instanceof ApiError ? err.message : "Retry failed to start.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleSaveConfig(config: {
    cloud_target: Project["cloud_target"];
    environment: Project["environment"];
    region: string;
    availability_requirement: Project["availability_requirement"];
    compliance_framework: Project["compliance_framework"];
  }) {
    if (!project) return { ok: false, error: "Project not loaded." };
    try {
      const updated = await patch<Project>(`/api/v1/projects/${projectId}`, config);
      setProject(updated);
      return { ok: true as const };
    } catch (err) {
      return {
        ok: false as const,
        error: err instanceof ApiError ? err.message : "Could not save configuration.",
      };
    }
  }

  async function handleExport() {
    const gen = activeGeneration;
    if (!gen) return;
    setExportBusy(true);
    setExportError(null);
    try {
      const { blob, filename } = await downloadFile(`/api/v1/generations/${gen.id}/export`);
      saveBlob(blob, filename || `cloudforge-project-${projectId}.zip`);
    } catch (err) {
      setExportError(err instanceof ApiError ? err.message : "Export failed.");
    } finally {
      setExportBusy(false);
    }
  }

  const isRunning = activeGeneration
    ? !TERMINAL_STATUSES.includes(activeGeneration.status)
    : generating;

  const availableTabs = useMemo(
    () =>
      TAB_DEFINITIONS.map((def) => ({
        key: def.type,
        label: def.label,
        disabled: !assetByType(def.type),
      })),
    [assetByType],
  );

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl space-y-4">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  if (pageError || !project) {
    return (
      <div className="mx-auto max-w-3xl">
        <ErrorBanner
          message={pageError ?? "Project not found."}
          title="Could not load project"
        />
        <button
          type="button"
          onClick={() => router.push("/dashboard")}
          className="mt-4 rounded-md border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:border-gray-700 dark:hover:bg-gray-800"
        >
          Back to dashboard
        </button>
      </div>
    );
  }

  const activeSummary = assetByType(activeTab as AssetType);
  const activeDef = tabDefinitionFor(activeTab as AssetType);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{project.name}</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Project Studio — {project.cloud_target} · {project.environment} · {project.region}
          </p>
        </div>
        {activeGeneration && (
          <button
            type="button"
            onClick={handleExport}
            disabled={exportBusy || activeGeneration.status !== "succeeded"}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 disabled:opacity-50"
          >
            {exportBusy ? "Preparing ZIP…" : "Download Complete Project"}
          </button>
        )}
      </div>

      {showDemoBanner && <DemoBanner provider={activeGeneration?.provider} />}
      {exportError && <ErrorBanner message={exportError} onDismiss={() => setExportError(null)} />}

      {/* Configuration */}
      <ConfigPanel project={project} onSave={handleSaveConfig} />

      {/* Natural-language input + generate */}
      <section
        aria-labelledby="prompt-heading"
        className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900"
      >
        <h2 id="prompt-heading" className="text-lg font-semibold">
          Requirements
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Describe the infrastructure you need. Be specific about resources, networking, and
          constraints.
        </p>
        <label htmlFor="nl-prompt" className="sr-only">
          Infrastructure requirements
        </label>
        <textarea
          id="nl-prompt"
          rows={5}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          aria-invalid={!!promptError}
          aria-describedby={promptError ? "nl-prompt-error" : "nl-prompt-hint"}
          className={`${inputClass} mt-3`}
          placeholder="Create an Azure virtual network with three subnets for AKS, Application Gateway, and Azure Bastion…"
        />
        <div className="mt-1 flex items-center justify-between">
          {promptError ? (
            <p id="nl-prompt-error" role="alert" className="text-sm text-red-600 dark:text-red-400">
              {promptError}
            </p>
          ) : (
            <p id="nl-prompt-hint" className="text-xs text-gray-500 dark:text-gray-400">
              Minimum {PROMPT_MIN_LENGTH} characters. Never paste raw cloud credentials or secrets
              into this field.
            </p>
          )}
          <span
            className="text-xs text-gray-500 dark:text-gray-400"
            aria-label={`${prompt.trim().length} characters entered`}
          >
            {prompt.trim().length}/{PROMPT_MIN_LENGTH}
          </span>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating || isRunning}
            className="rounded-md bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 disabled:opacity-50"
          >
            {generating || isRunning ? "Generating…" : "Generate"}
          </button>
          {isRunning && <Spinner label="Generation in progress — assets will appear as they complete." />}
        </div>
        {generateError && (
          <div className="mt-4">
            <ErrorBanner
              message={generateError}
              onDismiss={() => setGenerateError(null)}
              title="Generation failed"
            />
          </div>
        )}
        {activeGeneration && activeGeneration.status === "failed" && (
          <div className="mt-4 flex items-center gap-3 rounded-md border border-red-300 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950/40">
            <StatusBadge status="failed" />
            <p className="text-sm text-red-700 dark:text-red-300">
              {activeGeneration.error ?? "The generation failed."}
            </p>
            <button
              type="button"
              onClick={handleRetry}
              disabled={generating}
              className="ml-auto rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-500 disabled:opacity-50"
            >
              {generating ? "Retrying…" : "Retry"}
            </button>
          </div>
        )}
      </section>

      {/* Output area */}
      <section
        aria-labelledby="output-heading"
        className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900"
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 id="output-heading" className="text-lg font-semibold">
            Generated Output
          </h2>
          {activeGeneration && <StatusBadge status={activeGeneration.status} />}
        </div>

        {!activeGeneration ? (
          <EmptyState
            title="No output yet"
            description="Run Generate to produce architecture documentation, infrastructure-as-code, pipelines, and security guidance."
          />
        ) : assetsLoading ? (
          <Spinner label="Loading assets…" />
        ) : (
          <>
            <Tabs
              tabs={availableTabs}
              activeKey={activeTab}
              onChange={setActiveTab}
              ariaLabel="Generated asset tabs"
            />
            <div
              id={`tabpanel-${activeTab}`}
              role="tabpanel"
              aria-labelledby={`tab-${activeTab}`}
              className="pt-4"
            >
              {assetLoadingId ? (
                <Spinner label="Loading asset…" />
              ) : assetError ? (
                <ErrorBanner message={assetError} onDismiss={() => setAssetError(null)} />
              ) : activeSummary ? (
                <TabContent
                  summary={activeSummary}
                  content={assetContents[activeSummary.id] ?? ""}
                />
              ) : (
                <EmptyState
                  title={`No ${activeDef.label} output yet`}
                  description="This asset was not produced by the latest generation."
                />
              )}
            </div>
          </>
        )}
      </section>

      <p className="text-xs text-gray-500 dark:text-gray-400">
        Generated infrastructure must be reviewed by a qualified engineer before deployment.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Configuration panel
// ---------------------------------------------------------------------------

function ConfigPanel({
  project,
  onSave,
}: {
  project: Project;
  onSave: (config: {
    cloud_target: Project["cloud_target"];
    environment: Project["environment"];
    region: string;
    availability_requirement: Project["availability_requirement"];
    compliance_framework: Project["compliance_framework"];
  }) => Promise<{ ok: boolean; error?: string }>;
}) {
  const [cloudTarget, setCloudTarget] = useState(project.cloud_target);
  const [environment, setEnvironment] = useState(project.environment);
  const [region, setRegion] = useState(project.region ?? "");
  const [availability, setAvailability] = useState(project.availability_requirement);
  const [compliance, setCompliance] = useState(project.compliance_framework);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage(null);
    const result = await onSave({
      cloud_target: cloudTarget,
      environment,
      region: region.trim(),
      availability_requirement: availability,
      compliance_framework: compliance,
    });
    setBusy(false);
    setMessage(
      result.ok ? { ok: true, text: "Configuration saved." } : { ok: false, text: result.error ?? "Save failed." },
    );
  }

  return (
    <section
      aria-labelledby="config-heading"
      className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900"
    >
      <h2 id="config-heading" className="text-lg font-semibold">
        Project Configuration
      </h2>
      <form onSubmit={handleSave} className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <label htmlFor="cfg-cloud-target" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Cloud target
          </label>
          <select
            id="cfg-cloud-target"
            value={cloudTarget}
            onChange={(e) => setCloudTarget(e.target.value as Project["cloud_target"])}
            className={inputClass}
          >
            {CLOUD_TARGET_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="cfg-environment" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Environment
          </label>
          <select
            id="cfg-environment"
            value={environment}
            onChange={(e) => setEnvironment(e.target.value as Project["environment"])}
            className={inputClass}
          >
            {ENVIRONMENT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="cfg-region" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Region
          </label>
          <input
            id="cfg-region"
            type="text"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <label htmlFor="cfg-availability" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Availability requirement
          </label>
          <select
            id="cfg-availability"
            value={availability}
            onChange={(e) => setAvailability(e.target.value as Project["availability_requirement"])}
            className={inputClass}
          >
            {AVAILABILITY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="cfg-compliance" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Compliance framework
          </label>
          <select
            id="cfg-compliance"
            value={compliance}
            onChange={(e) => setCompliance(e.target.value as Project["compliance_framework"])}
            className={inputClass}
          >
            {COMPLIANCE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-end">
          <button
            type="submit"
            disabled={busy}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 disabled:opacity-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
          >
            {busy ? "Saving…" : "Save configuration"}
          </button>
        </div>
      </form>
      {message && (
        <p
          role="status"
          className={`mt-3 text-sm ${message.ok ? "text-green-700 dark:text-green-300" : "text-red-600 dark:text-red-400"}`}
        >
          {message.text}
        </p>
      )}
    </section>
  );
}

function TabContent({ summary, content }: { summary: AssetSummary; content: string }) {
  const def = tabDefinitionFor(summary.asset_type);

  if (!content) {
    return <Spinner label="Loading asset…" />;
  }

  if (summary.asset_type === "security") {
    return <SecurityReportView summary={summary} content={content} />;
  }
  if (summary.asset_type === "zero-trust") {
    return <ZeroTrustView summary={summary} content={content} />;
  }
  if (summary.asset_type === "cost") {
    return <CostView summary={summary} content={content} />;
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
