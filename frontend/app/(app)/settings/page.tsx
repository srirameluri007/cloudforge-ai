"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError, del, get, patch, post } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type {
  AiProviderSettings,
  AuditEvent,
  AuditEventListResponse,
  CredentialReference,
  CredentialReferenceInput,
} from "@/lib/types";
import { CREDENTIAL_AUTH_TYPE_OPTIONS, CREDENTIAL_PROVIDER_OPTIONS } from "@/lib/constants";
import ErrorBanner from "@/components/ErrorBanner";
import Spinner from "@/components/Spinner";
import ConfirmModal from "@/components/ConfirmModal";

const inputClass =
  "w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section
      aria-label={title}
      className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900"
    >
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export default function SettingsPage() {
  const router = useRouter();
  const { user, isAdmin, refresh } = useAuth();

  // profile
  const [name, setName] = useState("");
  const [profileMsg, setProfileMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [profileBusy, setProfileBusy] = useState(false);

  // AI provider
  const [aiSettings, setAiSettings] = useState<AiProviderSettings | null>(null);
  const [aiLoading, setAiLoading] = useState(true);

  // credentials
  const [creds, setCreds] = useState<CredentialReference[]>([]);
  const [credsLoading, setCredsLoading] = useState(true);
  const [credForm, setCredForm] = useState<CredentialReferenceInput>({
    name: "",
    provider: CREDENTIAL_PROVIDER_OPTIONS[0],
    auth_type: CREDENTIAL_AUTH_TYPE_OPTIONS[0],
    vault_reference: "",
    description: "",
  });
  const [credError, setCredError] = useState<string | null>(null);
  const [credBusy, setCredBusy] = useState(false);
  const [deleteCred, setDeleteCred] = useState<CredentialReference | null>(null);

  // account deletion
  const [deleteAccountOpen, setDeleteAccountOpen] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // audit
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.name) setName(String(user.name));
  }, [user]);

  useEffect(() => {
    let cancelled = false;
    get<AiProviderSettings>("/api/v1/settings/ai-provider")
      .then((s) => {
        if (!cancelled) setAiSettings(s);
      })
      .catch((err) => {
        if (!cancelled) setPageError(err instanceof ApiError ? err.message : "Could not load AI provider settings.");
      })
      .finally(() => {
        if (!cancelled) setAiLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const loadCreds = useCallback(async () => {
    setCredsLoading(true);
    try {
      const res = await get<{ items: CredentialReference[] }>("/api/v1/credential-references");
      setCreds(res.items ?? []);
    } catch (err) {
      setCredError(err instanceof ApiError ? err.message : "Could not load credential references.");
    } finally {
      setCredsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCreds();
  }, [loadCreds]);

  useEffect(() => {
    if (!isAdmin) return;
    let cancelled = false;
    setAuditLoading(true);
    get<AuditEventListResponse>("/api/v1/audit-events")
      .then((res) => {
        if (!cancelled) setAuditEvents(res.items ?? []);
      })
      .catch(() => {
        /* audit view is best-effort */
      })
      .finally(() => {
        if (!cancelled) setAuditLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isAdmin]);

  async function handleProfileSave(e: React.FormEvent) {
    e.preventDefault();
    setProfileBusy(true);
    setProfileMsg(null);
    try {
      await patch("/api/v1/users/me", { name: name.trim() });
      await refresh();
      setProfileMsg({ ok: true, text: "Profile updated." });
    } catch (err) {
      setProfileMsg({ ok: false, text: err instanceof ApiError ? err.message : "Could not update profile." });
    } finally {
      setProfileBusy(false);
    }
  }

  async function handleCreateCred(e: React.FormEvent) {
    e.preventDefault();
    setCredBusy(true);
    setCredError(null);
    try {
      const created = await post<CredentialReference>("/api/v1/credential-references", {
        name: credForm.name.trim(),
        provider: credForm.provider,
        auth_type: credForm.auth_type,
        vault_reference: credForm.vault_reference?.trim() || undefined,
        description: credForm.description?.trim() || undefined,
      });
      setCreds((prev) => [created, ...prev]);
      setCredForm({
        name: "",
        provider: CREDENTIAL_PROVIDER_OPTIONS[0],
        auth_type: CREDENTIAL_AUTH_TYPE_OPTIONS[0],
        vault_reference: "",
        description: "",
      });
    } catch (err) {
      setCredError(err instanceof ApiError ? err.message : "Could not create the credential reference.");
    } finally {
      setCredBusy(false);
    }
  }

  async function handleDeleteCred() {
    if (!deleteCred) return;
    try {
      await del(`/api/v1/credential-references/${deleteCred.id}`);
      setCreds((prev) => prev.filter((c) => c.id !== deleteCred.id));
    } catch (err) {
      setCredError(err instanceof ApiError ? err.message : "Could not delete the credential reference.");
    } finally {
      setDeleteCred(null);
    }
  }

  async function handleDeleteAccount() {
    setDeleteBusy(true);
    setDeleteError(null);
    try {
      await del("/api/v1/users/me");
      try {
        await post("/api/v1/auth/logout");
      } catch {
        /* best effort */
      }
      router.push("/");
      router.refresh();
    } catch (err) {
      setDeleteError(err instanceof ApiError ? err.message : "Could not delete the account.");
      setDeleteBusy(false);
    }
  }

  async function handleLogout() {
    try {
      await post("/api/v1/auth/logout");
    } catch {
      /* best effort */
    }
    router.push("/");
    router.refresh();
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      {pageError && <ErrorBanner message={pageError} onDismiss={() => setPageError(null)} />}

      <Section title="Profile">
        <form onSubmit={handleProfileSave} className="space-y-3">
          <div>
            <label htmlFor="profile-name" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Display name
            </label>
            <input
              id="profile-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <span className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Email</span>
            <p className="text-sm text-gray-600 dark:text-gray-400">{user?.email ?? "—"}</p>
          </div>
          {profileMsg && (
            <p
              role="status"
              className={`text-sm ${profileMsg.ok ? "text-green-700 dark:text-green-300" : "text-red-600 dark:text-red-400"}`}
            >
              {profileMsg.text}
            </p>
          )}
          <button
            type="submit"
            disabled={profileBusy || !name.trim()}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 disabled:opacity-50"
          >
            {profileBusy ? "Saving…" : "Save profile"}
          </button>
        </form>
      </Section>

      <Section title="AI Provider">
        {aiLoading ? (
          <Spinner label="Loading AI provider settings…" />
        ) : aiSettings ? (
          <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
            <div className="rounded-md border border-gray-200 p-3 dark:border-gray-800">
              <dt className="font-medium text-gray-500 dark:text-gray-400">Provider</dt>
              <dd className="mt-1 font-semibold">{aiSettings.provider}</dd>
            </div>
            <div className="rounded-md border border-gray-200 p-3 dark:border-gray-800">
              <dt className="font-medium text-gray-500 dark:text-gray-400">Configured</dt>
              <dd className="mt-1 font-semibold">{aiSettings.configured ? "Yes" : "No"}</dd>
            </div>
            <div className="rounded-md border border-gray-200 p-3 dark:border-gray-800">
              <dt className="font-medium text-gray-500 dark:text-gray-400">Demo mode</dt>
              <dd className="mt-1 font-semibold">{aiSettings.demo_mode ? "On" : "Off"}</dd>
            </div>
          </dl>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            AI provider settings are unavailable right now.
          </p>
        )}
      </Section>

      <Section title="Credential References">
        <div
          role="note"
          aria-label="Credential safety warning"
          className="mb-4 rounded-md border border-amber-300 bg-amber-50 p-3 dark:border-amber-700 dark:bg-amber-950/40"
        >
          <p className="text-sm font-semibold text-amber-900 dark:text-amber-100">
            Never paste raw cloud credentials or secrets into prompts or credential fields.
          </p>
          <p className="mt-1 text-sm text-amber-800 dark:text-amber-200/80">
            Credential references point at a secrets vault — CloudForge never stores secret values
            itself. Store only the vault reference, never the secret.
          </p>
        </div>

        {credError && (
          <div className="mb-4">
            <ErrorBanner message={credError} onDismiss={() => setCredError(null)} />
          </div>
        )}

        <form onSubmit={handleCreateCred} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label htmlFor="cred-name" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Name <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <input
              id="cred-name"
              type="text"
              required
              value={credForm.name}
              onChange={(e) => setCredForm({ ...credForm, name: e.target.value })}
              className={inputClass}
              placeholder="prod-azure-sp"
            />
          </div>
          <div>
            <label htmlFor="cred-provider" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Provider <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <select
              id="cred-provider"
              value={credForm.provider}
              onChange={(e) => setCredForm({ ...credForm, provider: e.target.value })}
              className={inputClass}
            >
              {CREDENTIAL_PROVIDER_OPTIONS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="cred-auth-type" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Auth type <span aria-hidden="true" className="text-red-500">*</span>
            </label>
            <select
              id="cred-auth-type"
              value={credForm.auth_type}
              onChange={(e) => setCredForm({ ...credForm, auth_type: e.target.value })}
              className={inputClass}
            >
              {CREDENTIAL_AUTH_TYPE_OPTIONS.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="cred-vault-ref" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Vault reference
            </label>
            <input
              id="cred-vault-ref"
              type="text"
              value={credForm.vault_reference ?? ""}
              onChange={(e) => setCredForm({ ...credForm, vault_reference: e.target.value })}
              className={inputClass}
              placeholder="vault://secrets/prod-azure-sp"
            />
          </div>
          <div className="sm:col-span-2">
            <label htmlFor="cred-description" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Description
            </label>
            <input
              id="cred-description"
              type="text"
              value={credForm.description ?? ""}
              onChange={(e) => setCredForm({ ...credForm, description: e.target.value })}
              className={inputClass}
            />
          </div>
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={credBusy || !credForm.name.trim()}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 disabled:opacity-50"
            >
              {credBusy ? "Adding…" : "Add credential reference"}
            </button>
          </div>
        </form>

        <div className="mt-6">
          <h3 className="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            Saved references
          </h3>
          {credsLoading ? (
            <Spinner label="Loading credential references…" />
          ) : creds.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">No credential references yet.</p>
          ) : (
            <ul className="divide-y divide-gray-200 rounded-md border border-gray-200 dark:divide-gray-800 dark:border-gray-800">
              {creds.map((cred) => (
                <li key={cred.id} className="flex items-center justify-between gap-3 p-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{cred.name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {cred.provider} · {cred.auth_type}
                      {cred.vault_reference ? ` · ${cred.vault_reference}` : ""}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setDeleteCred(cred)}
                    aria-label={`Delete credential reference ${cred.name}`}
                    className="rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-500 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-950/40"
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <ConfirmModal
          open={deleteCred !== null}
          title="Delete credential reference"
          message={
            deleteCred
              ? `Delete the credential reference "${deleteCred.name}"? Pipelines referencing it will fail until it is recreated.`
              : ""
          }
          confirmLabel="Delete"
          danger
          onConfirm={handleDeleteCred}
          onCancel={() => setDeleteCred(null)}
        />
      </Section>

      {isAdmin && (
        <Section title="Audit Log">
          {auditLoading ? (
            <Spinner label="Loading audit events…" />
          ) : auditEvents.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">No audit events recorded.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-800">
                    <th scope="col" className="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Time</th>
                    <th scope="col" className="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Action</th>
                    <th scope="col" className="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Actor</th>
                    <th scope="col" className="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Resource</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                  {auditEvents.map((event) => (
                    <tr key={event.id}>
                      <td className="px-3 py-2 text-gray-600 dark:text-gray-400">
                        {event.created_at ? new Date(event.created_at).toLocaleString() : "—"}
                      </td>
                      <td className="px-3 py-2">{event.action}</td>
                      <td className="px-3 py-2">{String(event.actor ?? "—")}</td>
                      <td className="px-3 py-2">{String(event.resource ?? "—")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>
      )}

      <Section title="Account">
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
        >
          Log out
        </button>
      </Section>

      <Section title="Delete Account">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Deleting your account permanently removes your profile, projects, and generated assets.
          This cannot be undone.
        </p>
        <button
          type="button"
          onClick={() => {
            setDeleteConfirmText("");
            setDeleteError(null);
            setDeleteAccountOpen(true);
          }}
          className="mt-3 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-500"
        >
          Delete my account
        </button>
      </Section>

      {deleteAccountOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setDeleteAccountOpen(false)}
            aria-hidden="true"
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-account-title"
            className="relative w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-gray-900"
          >
            <h2 id="delete-account-title" className="text-lg font-semibold text-red-700 dark:text-red-300">
              Delete account
            </h2>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              This is permanent. Type <strong>DELETE</strong> to confirm.
            </p>
            <label htmlFor="delete-confirm-input" className="sr-only">
              Type DELETE to confirm account deletion
            </label>
            <input
              id="delete-confirm-input"
              type="text"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              className={`${inputClass} mt-3`}
              placeholder="DELETE"
              autoComplete="off"
            />
            {deleteError && (
              <p role="alert" className="mt-2 text-sm text-red-600 dark:text-red-400">
                {deleteError}
              </p>
            )}
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setDeleteAccountOpen(false)}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteAccount}
                disabled={deleteConfirmText !== "DELETE" || deleteBusy}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-500 disabled:opacity-50"
              >
                {deleteBusy ? "Deleting…" : "Delete my account"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
