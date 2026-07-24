import { create } from "zustand";
import type { UserRead } from "@/lib/api/schemas/auth";

type AuthState = {
  accessToken: string | null;
  user: UserRead | null;
  /** true until the initial silent-refresh attempt on app load resolves. */
  isHydrating: boolean;
  setSession: (accessToken: string, user: UserRead) => void;
  clear: () => void;
  finishHydration: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isHydrating: true,
  setSession: (accessToken, user) => set({ accessToken, user, isHydrating: false }),
  clear: () => set({ accessToken: null, user: null, isHydrating: false }),
  finishHydration: () => set({ isHydrating: false }),
}));
