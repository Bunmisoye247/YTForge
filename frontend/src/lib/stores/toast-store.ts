import { create } from "zustand";

export type Toast = {
  id: number;
  message: string;
  tone: "success" | "error";
};

let nextId = 1;

type ToastState = {
  toasts: Toast[];
  push: (message: string, tone: Toast["tone"]) => void;
  dismiss: (id: number) => void;
};

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (message, tone) => {
    const id = nextId++;
    set((state) => ({ toasts: [...state.toasts, { id, message, tone }] }));
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    }, 4000);
  },
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));

export function useToast() {
  const push = useToastStore((s) => s.push);
  return {
    success: (message: string) => push(message, "success"),
    error: (message: string) => push(message, "error"),
  };
}
