import { apiClient } from "@/lib/api/client";
import { accessTokenResponseSchema, userReadSchema } from "@/lib/api/schemas/auth";
import type { AccessTokenResponse, RegisterRequest, UserRead } from "@/lib/api/schemas/auth";

export function register(data: RegisterRequest): Promise<UserRead> {
  return apiClient.post("/auth/register", userReadSchema, data);
}

export function login(email: string, password: string): Promise<AccessTokenResponse> {
  return apiClient.postForm("/auth/login", accessTokenResponseSchema, {
    username: email,
    password,
  });
}

export function refresh(): Promise<AccessTokenResponse> {
  return apiClient.post("/auth/refresh", accessTokenResponseSchema);
}

export function logout(): Promise<void> {
  return apiClient.post("/auth/logout", null);
}

export function me(): Promise<UserRead> {
  return apiClient.get("/auth/me", userReadSchema);
}
