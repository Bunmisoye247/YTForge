"use client";

import { useToastStore } from "@/lib/stores/toast-store";
import { cn } from "@/lib/utils/cn";

export function Toaster() {
  const { toasts, dismiss } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((toast) => (
        <button
          key={toast.id}
          onClick={() => dismiss(toast.id)}
          className={cn(
            "rounded-md px-4 py-2 text-left text-sm text-white shadow-lg",
            toast.tone === "success" ? "bg-[--color-success]" : "bg-[--color-danger]",
          )}
        >
          {toast.message}
        </button>
      ))}
    </div>
  );
}
