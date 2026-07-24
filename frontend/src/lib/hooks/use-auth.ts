"use client";

import { useMutation } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import * as authApi from "@/lib/api/endpoints/auth";
import { useAuthStore } from "@/lib/stores/auth-store";

export function useAuth() {
  const { accessToken, user, isHydrating, setSession, clear } = useAuthStore();
  return { accessToken, user, isHydrating, isAuthenticated: accessToken !== null, setSession, clear };
}

/** Runs once on app mount: attempts a silent refresh using the httpOnly
 * refresh cookie so a returning user doesn't have to log in again. */
export function useHydrateSession() {
  const attempted = useRef(false);
  const { setSession, finishHydration } = useAuthStore();

  useEffect(() => {
    if (attempted.current) return;
    attempted.current = true;

    authApi
      .refresh()
      .then((pair) => setSession(pair.access_token, pair.user))
      .catch(() => finishHydration());
  }, [setSession, finishHydration]);
}

export function useLoginMutation() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authApi.login(email, password),
    onSuccess: (pair) => setSession(pair.access_token, pair.user),
  });
}

export function useRegisterMutation() {
  return useMutation({
    mutationFn: authApi.register,
  });
}

export function useLogoutMutation() {
  const clear = useAuthStore((s) => s.clear);
  return useMutation({
    mutationFn: authApi.logout,
    onSettled: () => clear(),
  });
}
