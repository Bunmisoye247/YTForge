import type { z } from "zod";
import { ApiError, isProblemDetail } from "@/lib/api/errors";
import { accessTokenResponseSchema } from "@/lib/api/schemas/auth";
import { useAuthStore } from "@/lib/stores/auth-store";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  /** URL-encoded form body instead of JSON (used only by login). */
  form?: Record<string, string>;
  search?: URLSearchParams;
  /** Skip attaching the Authorization header and the 401-retry flow. */
  skipAuth?: boolean;
};

let refreshInFlight: Promise<boolean> | null = null;

/** Calls POST /auth/refresh directly (not via `request`) to avoid recursion. */
async function refreshSession(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    try {
      const response = await fetch(`${BASE_URL}${API_PREFIX}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) {
        useAuthStore.getState().clear();
        return false;
      }
      const parsed = accessTokenResponseSchema.parse(await response.json());
      useAuthStore.getState().setSession(parsed.access_token, parsed.user);
      return true;
    } catch {
      useAuthStore.getState().clear();
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

async function parseError(response: Response): Promise<ApiError> {
  let detail = response.statusText;
  let title = "Error";
  try {
    const body: unknown = await response.json();
    if (isProblemDetail(body)) {
      detail = body.detail;
      title = body.title;
    }
  } catch {
    // non-JSON error body (e.g. FastAPI validation 422 has its own shape)
  }
  return new ApiError(response.status, title, detail);
}

async function request<T>(
  path: string,
  schema: z.ZodType<T> | null,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, form, search, skipAuth = false } = options;

  const url = new URL(`${API_PREFIX}${path}`, BASE_URL);
  if (search) url.search = search.toString();

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (form !== undefined) headers["Content-Type"] = "application/x-www-form-urlencoded";
  if (!skipAuth) {
    const token = useAuthStore.getState().accessToken;
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const init: RequestInit = {
    method,
    headers,
    credentials: "include",
    body: form ? new URLSearchParams(form) : body !== undefined ? JSON.stringify(body) : undefined,
  };

  let response = await fetch(url, init);

  if (response.status === 401 && !skipAuth) {
    const refreshed = await refreshSession();
    if (refreshed) {
      const retryToken = useAuthStore.getState().accessToken;
      response = await fetch(url, {
        ...init,
        headers: { ...headers, Authorization: `Bearer ${retryToken}` },
      });
    }
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) return undefined as T;

  const json: unknown = await response.json();
  return schema ? schema.parse(json) : (json as T);
}

export const apiClient = {
  get: <T>(path: string, schema: z.ZodType<T>, search?: URLSearchParams) =>
    request(path, schema, { method: "GET", search }),
  post: <T>(path: string, schema: z.ZodType<T> | null, body?: unknown) =>
    request(path, schema, { method: "POST", body }),
  postForm: <T>(path: string, schema: z.ZodType<T>, form: Record<string, string>) =>
    request(path, schema, { method: "POST", form, skipAuth: true }),
  patch: <T>(path: string, schema: z.ZodType<T>, body?: unknown) =>
    request(path, schema, { method: "PATCH", body }),
  put: <T>(path: string, schema: z.ZodType<T>, body?: unknown) =>
    request(path, schema, { method: "PUT", body }),
};
