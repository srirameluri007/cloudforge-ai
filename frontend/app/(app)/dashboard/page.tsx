"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";
import { ApiError, del, get, post } from "@/lib/api";
import type { Project, ProjectCreateInput, ProjectListResponse } from "@/lib/types";
import ProjectForm from "@/components/ProjectForm";
import ConfirmModal from "@/components/ConfirmModal";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import ErrorBanner from "@/components/ErrorBanner";
import Spinner from "@/components/Spinner";
import { SkeletonCard } from "@/components/Skeleton";

function formatDate(iso?: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString(undefined, { dateStyle: "medium" });
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<Spinner label="Loading dashboard…" />}>
      <DashboardContent />
    </Suspense>
  );
}

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createBusy, setCreateBusy] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await get<ProjectListResponse>("/api/v1/projects");
      setProjects(res.items ?? []);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load projects.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (searchParams.get("new") === "1") {
      setCreateOpen(true);
    }
  }, [searchParams]);

  async function handleCreate(input: ProjectCreateInput) {
    setCreateBusy(true);
    setCreateError(null);
    try {
      const created = await post<Project>("/api/v1/projects", input);
      setCreateOpen(false);
      setProjects((prev) => [created, ...prev]);
      router.push(`/projects/${created.id}`);
    } catch (err) {
      setCreateError(err instanceof ApiError ? err.message : "Could not create the project.");
    } finally {
      setCreateBusy(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleteBusy(true);
    try {
      await del(`/api/v1/projects/${deleteTarget.id}`);
      setProjects((prev) => prev.filter((p) => p.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete the project.");
      setDeleteTarget(null);
    } finally {
      setDeleteBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button
          type="button"
          onClick={() => {
            setCreateError(null);
            setCreateOpen(true);
          }}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500"
        >
          Create Project
        </button>
      </div>

      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} onDismiss={() => setError(null)} />
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2" aria-label="Loading projects">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : projects.length === 0 ? (
        <EmptyState
          title="No projects yet"
          description="Create your first project, describe the infrastructure you need in plain language, and CloudForge AI will generate deployment-ready code."
          action={
            <button
              type="button"
              onClick={() => setCreateOpen(true)}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500"
            >
              Create your first project
            </button>
          }
        />
      ) : (
        <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2" aria-label="Projects">
          {projects.map((project) => (
            <li
              key={project.id}
              className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900"
            >
              <div className="flex items-start justify-between gap-3">
                <Link
                  href={`/projects/${project.id}`}
                  className="text-base font-semibold hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500"
                >
                  {project.name}
                </Link>
                {project.status && <StatusBadge status={project.status} />}
              </div>
              <dl className="mt-3 space-y-1 text-sm text-gray-600 dark:text-gray-400">
                <div className="flex gap-2">
                  <dt className="font-medium">Cloud:</dt>
                  <dd className="capitalize">{project.cloud_target}</dd>
                </div>
                <div className="flex gap-2">
                  <dt className="font-medium">Created:</dt>
                  <dd>{formatDate(project.created_at)}</dd>
                </div>
                <div className="flex gap-2">
                  <dt className="font-medium">Updated:</dt>
                  <dd>{formatDate(project.updated_at)}</dd>
                </div>
              </dl>
              <div className="mt-4 flex gap-2">
                <Link
                  href={`/projects/${project.id}`}
                  className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                >
                  Open
                </Link>
                <button
                  type="button"
                  onClick={() => setDeleteTarget(project)}
                  aria-label={`Delete project ${project.name}`}
                  className="rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-500 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-950/40"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setCreateOpen(false)}
            aria-hidden="true"
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-project-title"
            className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl dark:bg-gray-900"
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 id="create-project-title" className="text-lg font-semibold">
                Create Project
              </h2>
              <button
                type="button"
                onClick={() => setCreateOpen(false)}
                aria-label="Close create project dialog"
                className="rounded-md p-2 text-gray-600 hover:bg-gray-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                  <path d="M18 6 6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
            <ProjectForm
              onSubmit={handleCreate}
              submitLabel="Create project"
              busy={createBusy}
              serverError={createError}
            />
          </div>
        </div>
      )}

      <ConfirmModal
        open={deleteTarget !== null}
        title="Delete project"
        message={
          deleteTarget
            ? `Delete "${deleteTarget.name}"? This will permanently remove the project and its generated assets. This cannot be undone.`
            : ""
        }
        confirmLabel="Delete project"
        danger
        busy={deleteBusy}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
