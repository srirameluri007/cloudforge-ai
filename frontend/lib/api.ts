import type { ApiErrorBody } from "./types";

/**
 * Typed fetch client for the CloudForge AI backend.
 *
 * Base URL comes from NEXT_PUBLIC_API_URL. An empty string means relative
 * URLs (production: the browser calls /api/* on the frontend origin and the
 * Next.js rewrite proxy forwards them to the backend server-side). Unset
 * defaults to http://localhost:8000 (local development).
 * Every request is sent with credentials: "include" — session cookies are
 * HttpOnly, so the frontend never touches tokens.
 */

const envBase =
  typeof process !== "undefined" ? process.env.NEXT_PUBLIC_API_URL : undefined;
export const API_BASE: string = envBase ?? "http://localhost:8000";

export class ApiError extends Error {
  code: string;
  fields?: Record<string, string | string[]>;
  requestId?: string;
  status: number;

  constructor(status: number, body: ApiErrorBody | null, fallbackMessage: string) {
    const message = body?.error?.message ?? fallbackMessage;
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = body?.error?.code ?? "unknown_error";
    this.fields = body?.error?.fields;
    this.requestId = body?.error?.request_id;
  }
}

async function parseErrorBody(res: Response): Promise<ApiErrorBody | null> {
  try {
    const json = (await res.json()) as unknown;
    if (json && typeof json === "object" && "error" in json) {
      return json as ApiErrorBody;
    }
    return null;
  } catch {
    return null;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  /** Extra headers merged over the defaults. */
  headers?: Record<string, string>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, headers } = options;
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    credentials: "include",
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const errorBody = await parseErrorBody(res);
    throw new ApiError(res.status, errorBody, `Request failed with status ${res.status}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}

export function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

export function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body });
}

export function patch<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "PATCH", body });
}

export function del(path: string): Promise<void> {
  return request<void>(path, { method: "DELETE" });
}

/** Fetch an endpoint that returns a binary file and resolve with a Blob. */
export async function downloadFile(path: string): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
  });
  if (!res.ok) {
    const errorBody = await parseErrorBody(res);
    throw new ApiError(res.status, errorBody, `Download failed with status ${res.status}`);
  }
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const match = /filename\*?=(?:UTF-8'')?["']?([^"';\n]+)["']?/i.exec(disposition);
  const filename = match ? decodeURIComponent(match[1].trim()) : "download";
  return { blob, filename };
}

/** Trigger a browser download of a Blob under the given filename. */
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}
