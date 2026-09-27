"use client";

import { useState } from "react";
import type { Project, ProjectCreateInput } from "@/lib/types";
import {
  AVAILABILITY_OPTIONS,
  CLOUD_TARGET_OPTIONS,
  COMPLIANCE_OPTIONS,
  ENVIRONMENT_OPTIONS,
} from "@/lib/constants";

interface ProjectFormProps {
  initial?: Partial<Project>;
  onSubmit: (input: ProjectCreateInput) => Promise<void>;
  submitLabel?: string;
  busy?: boolean;
  serverError?: string | null;
}

const inputClass =
  "w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100";

export default function ProjectForm({
  initial,
  onSubmit,
  submitLabel = "Create project",
  busy = false,
  serverError = null,
}: ProjectFormProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [cloudTarget, setCloudTarget] = useState<ProjectCreateInput["cloud_target"]>(
    initial?.cloud_target ?? "azure",
  );
  const [environment, setEnvironment] = useState<ProjectCreateInput["environment"]>(
    initial?.environment ?? "development",
  );
  const [region, setRegion] = useState(initial?.region ?? "");
  const [availability, setAvailability] = useState<ProjectCreateInput["availability_requirement"]>(
    initial?.availability_requirement ?? "standard",
  );
  const [compliance, setCompliance] = useState<ProjectCreateInput["compliance_framework"]>(
    initial?.compliance_framework ?? "none",
  );
  const [errors, setErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const next: Record<string, string> = {};
    if (!name.trim()) next.name = "Project name is required.";
    if (!region.trim()) next.region = "Region is required (e.g. eastus).";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    await onSubmit({
      name: name.trim(),
      description: description.trim() || undefined,
      original_prompt: initial?.original_prompt,
      cloud_target: cloudTarget,
      environment,
      region: region.trim(),
      availability_requirement: availability,
      compliance_framework: compliance,
    });
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div>
        <label htmlFor="project-name" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Project name <span aria-hidden="true" className="text-red-500">*</span>
        </label>
        <input
          id="project-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          aria-invalid={!!errors.name}
          aria-describedby={errors.name ? "project-name-error" : undefined}
          className={inputClass}
          placeholder="Azure Network Demo"
        />
        {errors.name && (
          <p id="project-name-error" role="alert" className="mt-1 text-sm text-red-600 dark:text-red-400">
            {errors.name}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="project-description" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Description
        </label>
        <textarea
          id="project-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className={inputClass}
          placeholder="Optional short description"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="project-cloud-target" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Cloud target <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <select
            id="project-cloud-target"
            value={cloudTarget}
            onChange={(e) => setCloudTarget(e.target.value as ProjectCreateInput["cloud_target"])}
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
          <label htmlFor="project-environment" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Environment <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <select
            id="project-environment"
            value={environment}
            onChange={(e) => setEnvironment(e.target.value as ProjectCreateInput["environment"])}
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
          <label htmlFor="project-region" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Region <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <input
            id="project-region"
            type="text"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            required
            aria-invalid={!!errors.region}
            aria-describedby={errors.region ? "project-region-error" : "project-region-hint"}
            className={inputClass}
            placeholder="eastus"
          />
          {errors.region ? (
            <p id="project-region-error" role="alert" className="mt-1 text-sm text-red-600 dark:text-red-400">
              {errors.region}
            </p>
          ) : (
            <p id="project-region-hint" className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Provider region, e.g. eastus, westeurope, us-east-1.
            </p>
          )}
        </div>
        <div>
          <label htmlFor="project-availability" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Availability <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <select
            id="project-availability"
            value={availability}
            onChange={(e) => setAvailability(e.target.value as ProjectCreateInput["availability_requirement"])}
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
          <label htmlFor="project-compliance" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Compliance framework <span aria-hidden="true" className="text-red-500">*</span>
          </label>
          <select
            id="project-compliance"
            value={compliance}
            onChange={(e) => setCompliance(e.target.value as ProjectCreateInput["compliance_framework"])}
            className={inputClass}
          >
            {COMPLIANCE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {serverError && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {serverError}
        </p>
      )}

      <button
        type="submit"
        disabled={busy}
        className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 disabled:opacity-50"
      >
        {busy ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}
