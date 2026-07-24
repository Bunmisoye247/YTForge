import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";
import { apiClient } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { useAuthStore } from "@/lib/stores/auth-store";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("apiClient", () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: "initial-token", user: null, isHydrating: false });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("parses a successful response through the given schema", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ value: "hello" })));
    const result = await apiClient.get("/ping", z.object({ value: z.string() }));
    expect(result.value).toBe("hello");
  });

  it("throws an ApiError with the RFC 7807 detail on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({ type: "about:blank", title: "NotFoundError", status: 404, detail: "Project not found" }, 404),
      ),
    );
    await expect(apiClient.get("/projects/missing", z.object({}))).rejects.toMatchObject({
      status: 404,
      message: "Project not found",
    });
  });

  it("refreshes the access token once on 401 and retries the original request", async () => {
    const fetchMock = vi
      .fn()
      // first call: the original request, unauthorized
      .mockResolvedValueOnce(jsonResponse({ detail: "expired" }, 401))
      // second call: POST /auth/refresh succeeds
      .mockResolvedValueOnce(
        jsonResponse({
          access_token: "new-token",
          token_type: "bearer",
          user: {
            id: "018f1b1e-0000-7000-8000-000000000000",
            email: "a@example.com",
            full_name: "A",
            is_active: true,
            is_superuser: false,
          },
        }),
      )
      // third call: the retried original request, now authorized
      .mockResolvedValueOnce(jsonResponse({ value: "recovered" }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiClient.get("/protected", z.object({ value: z.string() }));

    expect(result.value).toBe("recovered");
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(useAuthStore.getState().accessToken).toBe("new-token");
  });

  it("clears the session if refresh also fails after a 401", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ detail: "expired" }, 401))
      .mockResolvedValueOnce(jsonResponse({ detail: "invalid refresh token" }, 401));
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiClient.get("/protected", z.object({}))).rejects.toBeInstanceOf(ApiError);
    expect(useAuthStore.getState().accessToken).toBeNull();
  });
});
